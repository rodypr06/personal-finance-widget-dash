"""
FastAPI application for Personal Finance Automation.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import engine, get_db
from app.routers import ingest, categorize, reports, alerts

# Template and static file paths
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = BASE_DIR / "static"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Finance Automation API")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Log DB without credentials
    logger.info(f"OpenAI Model: {settings.OPENAI_MODEL}")

    yield

    # Shutdown
    logger.info("Shutting down Finance Automation API")
    await engine.dispose()
    logger.info("Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="Personal Finance Automation API",
    description="""
    Automated personal finance tracking with intelligent categorization.

    ## Features

    * **Transaction Ingestion**: Import transactions from statements
    * **Smart Categorization**: Rule-based + AI-powered categorization
    * **Reporting**: Monthly summaries, trends, and insights
    * **Alerts**: Anomaly detection and notifications

    ## Authentication

    Write endpoints require JWT authentication via Bearer token.
    Read-only endpoints are public for dashboard access.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database error occurred",
            "type": "database_error"
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "type": "validation_error"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Root endpoint - Dashboard
@app.get("/", tags=["UI"], include_in_schema=False)
async def dashboard(request: Request):
    """
    Main dashboard view.

    Renders the glassmorphic dashboard with transaction summaries,
    charts, and recent activity.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


# Reports page
@app.get("/reports", tags=["UI"], include_in_schema=False)
async def reports_page(request: Request):
    """
    Reports view.

    Renders the advanced reporting interface with filters,
    charts, and detailed transaction tables.
    """
    return templates.TemplateResponse(
        "reports.html",
        {"request": request}
    )


# API root endpoint
@app.get("/api", tags=["Health"])
async def api_root():
    """
    API root endpoint returning service status.

    Returns basic service information.
    """
    return {
        "status": "ok",
        "service": "finance-automation",
        "version": "1.0.0"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Verifies database connectivity and service health.

    Returns:
        - status: Service status (healthy/unhealthy)
        - database: Database connection status
        - version: API version
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "version": "1.0.0"
    }

    # Check database connection
    try:
        async for db in get_db():
            # Simple query to test connection
            await db.execute("SELECT 1")
            health_status["database"] = "connected"
            break
    except Exception as e:
        logger.error(f"Health check failed - database error: {e}")
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
        return JSONResponse(
            status_code=503,
            content=health_status
        )

    return health_status


# Include routers
app.include_router(
    ingest.router,
    prefix="/api",
    tags=["Ingestion"]
)

app.include_router(
    categorize.router,
    prefix="/api",
    tags=["Categorization"]
)

app.include_router(
    reports.router,
    prefix="/api",
    tags=["Reports"]
)

app.include_router(
    alerts.router,
    prefix="/api",
    tags=["Alerts"]
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
