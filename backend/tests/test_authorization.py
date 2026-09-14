import pytest
from app.database import SessionLocal
from app.models.product import Product


class TestAuthorization:
    def test_admin_can_create_product(self, client, admin_headers):
        """Admin should be able to create products."""
        response = client.post("/api/products", json={
            "name": "Test Product",
            "category": "Electronics",
            "price": 99.99,
            "quantity": 10,
            "minimum_stock": 5,
        }, headers=admin_headers)
        assert response.status_code == 201

    def test_staff_cannot_create_product(self, client, staff_headers):
        """Staff should not be able to create products."""
        response = client.post("/api/products", json={
            "name": "Test Product",
            "category": "Electronics",
            "price": 99.99,
            "quantity": 10,
            "minimum_stock": 5,
        }, headers=staff_headers)
        assert response.status_code == 403

    def test_staff_can_view_products(self, client, staff_headers, admin_user):
        """Staff should be able to view products."""
        # Admin creates a product first
        db = SessionLocal()
        product = Product(name="Test", category="Cat", price=10, quantity=5, minimum_stock=2)
        db.add(product)
        db.commit()
        db.close()

        response = client.get("/api/products", headers=staff_headers)
        assert response.status_code == 200

    def test_admin_can_delete_product(self, client, admin_headers, admin_user):
        """Admin should be able to delete products."""
        # Create a product first
        db = SessionLocal()
        product = Product(name="To Delete", category="Cat", price=10, quantity=5, minimum_stock=2)
        db.add(product)
        db.commit()
        db.refresh(product)
        product_id = product.id
        db.close()

        response = client.delete(f"/api/products/{product_id}", headers=admin_headers)
        assert response.status_code == 204

    def test_staff_cannot_delete_product(self, client, staff_headers, admin_user):
        """Staff should not be able to delete products."""
        db = SessionLocal()
        product = Product(name="To Delete", category="Cat", price=10, quantity=5, minimum_stock=2)
        db.add(product)
        db.commit()
        db.refresh(product)
        product_id = product.id
        db.close()

        response = client.delete(f"/api/products/{product_id}", headers=staff_headers)
        assert response.status_code == 403

    def test_unauthenticated_access(self, client):
        """Unauthenticated users cannot access protected endpoints."""
        response = client.get("/api/products")
        assert response.status_code == 401

    def test_staff_can_view_sales(self, client, staff_headers):
        """Staff should be able to view sales."""
        response = client.get("/api/sales", headers=staff_headers)
        assert response.status_code == 200

    def test_staff_can_view_dashboard(self, client, staff_headers):
        """Staff should be able to view dashboard."""
        response = client.get("/api/dashboard", headers=staff_headers)
        assert response.status_code == 200

    def test_staff_can_view_ai_predictions(self, client, staff_headers):
        """Staff should be able to view AI predictions."""
        response = client.get("/api/ai/demand-prediction", headers=staff_headers)
        assert response.status_code == 200
