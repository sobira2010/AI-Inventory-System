from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import CORSErrorResponseMiddleware
from app.routers import auth, products, sales, stock, dashboard, ai
from app.api import agent

app = FastAPI(
    title="AI Inventory Management System",
    description="A full-stack AI-powered inventory management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware is added before the app starts serving requests, at import time.
# Order matters: add_middleware() prepends, so the LAST middleware added is the
# OUTERMOST. CORSMiddleware is added first (inner) and CORSErrorResponseMiddleware
# last (outer), so unhandled exceptions and other error responses pass through the
# error middleware on the way out and get Access-Control-Allow-Origin stamped on,
# instead of bypassing CORS entirely and surfacing in the browser as
# "No 'Access-Control-Allow-Origin' header is present".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CORSErrorResponseMiddleware)


@app.on_event("startup")
def init_database() -> None:
    """Apply Alembic migrations so all tables exist (no-op when up to date).

    Production (Neon PostgreSQL) must have the schema ready before the first
    request; local SQLite development is skipped inside run_migrations().
    """
    from app.startup_db import run_migrations

    run_migrations()


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
