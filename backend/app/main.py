from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, products, sales, stock, dashboard, ai
from app.api import agent

app = FastAPI(
    title="AI Inventory Management System",
    description="A full-stack AI-powered inventory management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(stock.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(agent.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "AI Inventory Management System API", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
