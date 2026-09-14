import pytest
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.product import Product
from app.models.sale import Sale


class TestAI:
    def test_demand_prediction_insufficient_data(self, client, staff_headers):
        """Test demand prediction with insufficient data."""
        response = client.get("/api/ai/demand-prediction", headers=staff_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data

    def test_demand_prediction_with_data(self, client, staff_headers):
        """Test demand prediction with sufficient sales data."""
        db = SessionLocal()
        product = Product(name="Test Product", category="Test", price=10.0, quantity=100, minimum_stock=10)
        db.add(product)
        db.commit()
        db.refresh(product)

        # Create multiple sales over time
        for i in range(10):
            sale = Sale(
                product_id=product.id,
                quantity=5,
                unit_price=10.0,
                total_price=50.0,
                sold_by=1,
                sale_date=datetime.utcnow() - timedelta(days=i),
            )
            db.add(sale)
        db.commit()
        db.close()

        response = client.get("/api/ai/demand-prediction", headers=staff_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) > 0

    def test_low_stock_prediction(self, client, staff_headers):
        """Test low stock prediction."""
        response = client.get("/api/ai/low-stock-prediction", headers=staff_headers)
        assert response.status_code == 200
        assert "predictions" in response.json()

    def test_reorder_recommendations(self, client, staff_headers):
        """Test reorder recommendations."""
        response = client.get("/api/ai/reorder-recommendations", headers=staff_headers)
        assert response.status_code == 200
        assert "recommendations" in response.json()

    def test_ai_requires_auth(self, client):
        """Test that AI endpoints require authentication."""
        response = client.get("/api/ai/demand-prediction")
        assert response.status_code == 401
