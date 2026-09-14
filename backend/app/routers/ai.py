from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai_service import predict_demand, predict_low_stock, get_reorder_recommendations
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["AI Predictions"])


@router.get("/demand-prediction")
def demand_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get demand predictions for all products using ML models."""
    predictions = predict_demand(db)
    return {
        "predictions": predictions,
        "total": len(predictions),
    }


@router.get("/low-stock-prediction")
def low_stock_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get low stock predictions based on historical sales trends."""
    predictions = predict_low_stock(db)
    return {
        "predictions": predictions,
        "total": len(predictions),
    }


@router.get("/reorder-recommendations")
def reorder_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get reorder recommendations based on predicted demand and current stock."""
    recommendations = get_reorder_recommendations(db)
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }
