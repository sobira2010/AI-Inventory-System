import pytest
from app.database import SessionLocal
from app.models.product import Product


class TestProducts:
    def test_create_product(self, client, admin_headers):
        """Test creating a product."""
        response = client.post("/api/products", json={
            "name": "Laptop",
            "category": "Electronics",
            "description": "A high-performance laptop",
            "price": 999.99,
            "quantity": 50,
            "minimum_stock": 10,
            "supplier": "Tech Corp",
        }, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Laptop"
        assert data["price"] == 999.99
        assert data["quantity"] == 50

    def test_create_product_validation(self, client, admin_headers):
        """Test product validation."""
        response = client.post("/api/products", json={
            "name": "",
            "category": "Electronics",
            "price": -10,
            "quantity": 50,
            "minimum_stock": 10,
        }, headers=admin_headers)
        assert response.status_code == 422

    def test_list_products(self, client, admin_headers):
        """Test listing products."""
        # Create products
        for i in range(5):
            client.post("/api/products", json={
                "name": f"Product {i}",
                "category": "Test",
                "price": 10.0,
                "quantity": 10,
                "minimum_stock": 2,
            }, headers=admin_headers)

        response = client.get("/api/products", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["products"]) == 5

    def test_get_product(self, client, admin_headers):
        """Test getting a single product."""
        # Create product
        create_response = client.post("/api/products", json={
            "name": "Test Product",
            "category": "Test",
            "price": 25.0,
            "quantity": 100,
            "minimum_stock": 10,
        }, headers=admin_headers)
        product_id = create_response.json()["id"]

        response = client.get(f"/api/products/{product_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Test Product"

    def test_get_nonexistent_product(self, client, admin_headers):
        """Test getting a non-existent product."""
        response = client.get("/api/products/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_update_product(self, client, admin_headers):
        """Test updating a product."""
        # Create product
        create_response = client.post("/api/products", json={
            "name": "Original Name",
            "category": "Test",
            "price": 10.0,
            "quantity": 50,
            "minimum_stock": 5,
        }, headers=admin_headers)
        product_id = create_response.json()["id"]

        # Update
        response = client.put(f"/api/products/{product_id}", json={
            "name": "Updated Name",
            "price": 15.0,
        }, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["price"] == 15.0

    def test_delete_product(self, client, admin_headers):
        """Test deleting a product."""
        create_response = client.post("/api/products", json={
            "name": "To Delete",
            "category": "Test",
            "price": 10.0,
            "quantity": 10,
            "minimum_stock": 2,
        }, headers=admin_headers)
        product_id = create_response.json()["id"]

        response = client.delete(f"/api/products/{product_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/products/{product_id}", headers=admin_headers)
        assert get_response.status_code == 404

    def test_search_products(self, client, admin_headers):
        """Test product search."""
        client.post("/api/products", json={
            "name": "Gaming Laptop",
            "category": "Electronics",
            "price": 1500.0,
            "quantity": 10,
            "minimum_stock": 2,
        }, headers=admin_headers)

        response = client.get("/api/products", params={"search": "Gaming"}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["products"][0]["name"] == "Gaming Laptop"

    def test_filter_by_category(self, client, admin_headers):
        """Test filtering by category."""
        client.post("/api/products", json={
            "name": "Product A",
            "category": "Category1",
            "price": 10.0,
            "quantity": 10,
            "minimum_stock": 2,
        }, headers=admin_headers)

        client.post("/api/products", json={
            "name": "Product B",
            "category": "Category2",
            "price": 20.0,
            "quantity": 10,
            "minimum_stock": 2,
        }, headers=admin_headers)

        response = client.get("/api/products", params={"category": "Category1"}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1
