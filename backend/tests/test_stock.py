import pytest
from app.database import SessionLocal
from app.models.product import Product


class TestStock:
    def _create_product(self, db, name="Test Product", quantity=50, min_stock=10):
        """Helper to create a product directly in DB."""
        product = Product(name=name, category="Test", price=10.0, quantity=quantity, minimum_stock=min_stock)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def test_add_stock(self, client, staff_headers):
        """Test adding stock."""
        db = SessionLocal()
        product = self._create_product(db, quantity=50)
        db.close()

        response = client.post("/api/stock/adjust", json={
            "product_id": product.id,
            "quantity_change": 20,
            "reason": "Restock",
        }, headers=staff_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["previous_quantity"] == 50
        assert data["new_quantity"] == 70
        assert data["quantity_change"] == 20

    def test_remove_stock(self, client, staff_headers):
        """Test removing stock."""
        db = SessionLocal()
        product = self._create_product(db, quantity=50)
        db.close()

        response = client.post("/api/stock/adjust", json={
            "product_id": product.id,
            "quantity_change": -10,
            "reason": "Damaged",
        }, headers=staff_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["new_quantity"] == 40

    def test_insufficient_stock_for_removal(self, client, staff_headers):
        """Test removing more stock than available."""
        db = SessionLocal()
        product = self._create_product(db, quantity=5)
        db.close()

        response = client.post("/api/stock/adjust", json={
            "product_id": product.id,
            "quantity_change": -10,
            "reason": "Damaged",
        }, headers=staff_headers)
        assert response.status_code == 400

    def test_stock_history(self, client, staff_headers):
        """Test getting stock history."""
        db = SessionLocal()
        product = self._create_product(db)
        db.close()

        # Make some adjustments
        client.post("/api/stock/adjust", json={
            "product_id": product.id,
            "quantity_change": 10,
            "reason": "Restock",
        }, headers=staff_headers)

        client.post("/api/stock/adjust", json={
            "product_id": product.id,
            "quantity_change": -5,
            "reason": "Damaged",
        }, headers=staff_headers)

        response = client.get("/api/stock/history", headers=staff_headers)
        assert response.status_code == 200
        history = response.json()["history"]
        assert len(history) >= 2

    def test_stock_adjust_nonexistent_product(self, client, staff_headers):
        """Test adjusting stock for non-existent product."""
        response = client.post("/api/stock/adjust", json={
            "product_id": 99999,
            "quantity_change": 10,
            "reason": "Restock",
        }, headers=staff_headers)
        assert response.status_code == 404
