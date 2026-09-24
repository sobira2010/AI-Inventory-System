from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import CORSErrorResponseMiddleware
from app.routers import auth, products, sales, stock, dashboard, ai
from app.api import agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Kick off (non-blocking) database schema init, then serve immediately.

    Render runs ``uvicorn app.main:app --host 0.0.0.0 --port $PORT`` and then
    scans for an open port. The database init must never delay the bind:
    ensure_schema_async() spawns a background thread and returns at once, so
    the port opens even if Neon is slow or unreachable (a previous synchronous
    startup hook caused "Port scan timeout reached, no open ports detected").

    Schema work runs in a daemon thread using the project's existing Alembic
    migrations; failures are logged and database errors then surface
    per-request. Local SQLite development skips it entirely (app.startup_db).
    """
    from app.startup_db import ensure_schema_async

    ensure_schema_async()
    yield


app = FastAPI(
    title="AI Inventory Management System",
    description="A full-stack AI-powered inventory management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
