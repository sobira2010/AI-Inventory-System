import pytest
from app.database import SessionLocal
from app.models.product import Product


class TestSales:
    def _create_product(self, db, name="Test Product", price=10.0, quantity=100, min_stock=10):
        """Helper to create a product directly in DB."""
        product = Product(name=name, category="Test", price=price, quantity=quantity, minimum_stock=min_stock)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def test_create_sale(self, client, staff_headers):
        """Test creating a sale."""
        db = SessionLocal()
        product = self._create_product(db, price=25.0, quantity=50)
        db.close()

        response = client.post("/api/sales", json={
            "product_id": product.id,
            "quantity": 5,
        }, headers=staff_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["quantity"] == 5
        assert data["unit_price"] == 25.0
        assert data["total_price"] == 125.0

    def test_sale_reduces_stock(self, client, staff_headers):
        """Test that a sale reduces product stock."""
        db = SessionLocal()
        product = self._create_product(db, quantity=50)
        db.close()

        client.post("/api/sales", json={
            "product_id": product.id,
            "quantity": 10,
        }, headers=staff_headers)

        # Check stock was reduced
        db = SessionLocal()
        updated_product = db.query(Product).filter(Product.id == product.id).first()
        assert updated_product.quantity == 40
        db.close()

    def test_sale_insufficient_stock(self, client, staff_headers):
        """Test sale with insufficient stock."""
        db = SessionLocal()
        product = self._create_product(db, quantity=5)
        db.close()

        response = client.post("/api/sales", json={
            "product_id": product.id,
            "quantity": 10,
        }, headers=staff_headers)
        assert response.status_code == 400

    def test_sale_nonexistent_product(self, client, staff_headers):
        """Test sale for non-existent product."""
        response = client.post("/api/sales", json={
            "product_id": 99999,
            "quantity": 1,
        }, headers=staff_headers)
        assert response.status_code == 404

    def test_list_sales(self, client, staff_headers):
        """Test listing sales."""
        response = client.get("/api/sales", headers=staff_headers)
        assert response.status_code == 200

    def test_get_sale(self, client, staff_headers):
        """Test getting a single sale."""
        db = SessionLocal()
        product = self._create_product(db)
        db.close()

        # Create sale
        create_response = client.post("/api/sales", json={
            "product_id": product.id,
            "quantity": 3,
        }, headers=staff_headers)
        sale_id = create_response.json()["id"]

        response = client.get(f"/api/sales/{sale_id}", headers=staff_headers)
        assert response.status_code == 200
        assert response.json()["quantity"] == 3

    def test_sale_creates_stock_history(self, client, staff_headers):
        """Test that a sale creates a stock history record."""
        db = SessionLocal()
        product = self._create_product(db, quantity=50)
        db.close()

        client.post("/api/sales", json={
            "product_id": product.id,
            "quantity": 5,
        }, headers=staff_headers)

        # Check stock history
        response = client.get("/api/stock/history", params={"product_id": product.id}, headers=staff_headers)
        assert response.status_code == 200
        history = response.json()["history"]
        assert len(history) > 0
        assert history[0]["quantity_change"] == -5
        assert history[0]["previous_quantity"] == 50
        assert history[0]["new_quantity"] == 45
