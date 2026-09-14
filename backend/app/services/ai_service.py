import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.sale import Sale


def get_sales_dataframe(db: Session, product_id: Optional[int] = None) -> pd.DataFrame:
    """Get sales data as a DataFrame."""
    query = db.query(Sale)
    if product_id:
        query = query.filter(Sale.product_id == product_id)

    sales = query.all()

    if not sales:
        return pd.DataFrame()

    data = []
    for sale in sales:
        data.append({
            "product_id": sale.product_id,
            "quantity": sale.quantity,
            "total_price": sale.total_price,
            "sale_date": sale.sale_date,
        })

    return pd.DataFrame(data)


def predict_demand(db: Session) -> list[dict]:
    """Predict future demand for each product based on historical sales."""
    products = db.query(Product).all()
    predictions = []

    for product in products:
        # Get sales for this product
        sales = db.query(Sale).filter(Sale.product_id == product.id).all()

        if len(sales) < 2:
            predictions.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.quantity,
                "predicted_demand": 0,
                "risk_level": "LOW",
                "message": "Not enough data for reliable prediction.",
            })
            continue

        # Create time series
        dates = [s.sale_date for s in sales]
        quantities = [s.quantity for s in sales]

        df = pd.DataFrame({"date": dates, "quantity": quantities})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Calculate average daily demand
        date_range = (df["date"].max() - df["date"].min()).days + 1
        total_quantity = df["quantity"].sum()
        avg_daily_demand = total_quantity / max(date_range, 1)

        # Simple trend analysis using linear regression
        from sklearn.linear_model import LinearRegression

        X = np.array(range(len(df))).reshape(-1, 1)
        y = df["quantity"].values

        model = LinearRegression()
        model.fit(X, y)

        # Predict next 7 days demand
        future_X = np.array(range(len(df), len(df) + 7)).reshape(-1, 1)
        predicted_quantities = model.predict(future_X)
        predicted_total = max(0, predicted_quantities.sum())

        # Determine risk level
        if product.quantity == 0:
            risk = "HIGH"
        elif product.quantity <= predicted_total * 0.5:
            risk = "HIGH"
        elif product.quantity <= predicted_total:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        predictions.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.quantity,
            "predicted_demand": round(predicted_total, 0),
            "risk_level": risk,
            "message": None,
        })

    return predictions


def predict_low_stock(db: Session) -> list[dict]:
    """Predict products that may become low stock based on historical trends."""
    products = db.query(Product).all()
    predictions = []

    for product in products:
        sales = db.query(Sale).filter(Sale.product_id == product.id).all()

        if len(sales) < 2:
            predictions.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.quantity,
                "minimum_stock": product.minimum_stock,
                "days_until_low_stock": None,
                "risk_level": "LOW",
                "message": "Not enough data for reliable prediction.",
            })
            continue

        # Calculate average daily sales
        quantities = [s.quantity for s in sales]
        avg_daily_sales = sum(quantities) / len(quantities)

        if avg_daily_sales == 0:
            predictions.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.quantity,
                "minimum_stock": product.minimum_stock,
                "days_until_low_stock": None,
                "risk_level": "LOW",
                "message": "No recent sales activity.",
            })
            continue

        # Calculate days until stock reaches minimum level
        stock_above_min = product.quantity - product.minimum_stock
        days_until_low = int(stock_above_min / avg_daily_sales) if stock_above_min > 0 else 0

        if days_until_low <= 3:
            risk = "HIGH"
        elif days_until_low <= 7:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        predictions.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.quantity,
            "minimum_stock": product.minimum_stock,
            "days_until_low_stock": days_until_low,
            "risk_level": risk,
            "message": None,
        })

    return predictions


def get_reorder_recommendations(db: Session) -> list[dict]:
    """Calculate recommended reorder quantities based on current stock and predicted demand."""
    products = db.query(Product).all()
    recommendations = []

    for product in products:
        sales = db.query(Sale).filter(Sale.product_id == product.id).all()

        if len(sales) < 2:
            recommendations.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.quantity,
                "predicted_demand": 0,
                "recommended_reorder": 0,
                "risk_level": "LOW",
                "message": "Not enough data for reliable prediction.",
            })
            continue

        # Calculate average daily demand
        quantities = [s.quantity for s in sales]
        avg_daily_demand = sum(quantities) / len(quantities)

        # Predict next 30 days demand
        predicted_30_day = avg_daily_demand * 30

        # Recommended reorder = predicted demand + safety stock (20%) - current stock
        safety_stock = predicted_30_day * 0.2
        recommended = max(0, predicted_30_day + safety_stock - product.quantity)

        # Determine risk
        if product.quantity == 0:
            risk = "HIGH"
        elif product.quantity <= product.minimum_stock:
            risk = "HIGH"
        elif product.quantity <= predicted_30_day:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        recommendations.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.quantity,
            "predicted_demand": round(predicted_30_day, 0),
            "recommended_reorder": round(recommended, 0),
            "risk_level": risk,
            "message": None,
        })

    return recommendations
