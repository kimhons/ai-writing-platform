"""
WriteCrew Backend - Main FastAPI Application
Multi-agentic AI writing platform with CrewAI integration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config.settings import get_settings
from .api.routes import agents, health, websocket
from .services.crew_orchestrator import CrewOrchestrator
from .services.database import DatabaseService
from .services.redis_service import RedisService
from .models.database import init_db
from .utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global services
crew_orchestrator: CrewOrchestrator = None
db_service: DatabaseService = None
redis_service: RedisService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global crew_orchestrator, db_service, redis_service
    
    settings = get_settings()
    logger.info("Starting WriteCrew Backend", version="1.0.0")
    
    try:
        # Initialize database
        logger.info("Initializing database connection")
        await init_db()
        db_service = DatabaseService()
        
        # Initialize Redis
        logger.info("Initializing Redis connection")
        redis_service = RedisService(settings.redis_url)
        await redis_service.connect()
        
        # Initialize CrewAI orchestrator
        logger.info("Initializing CrewAI orchestrator")
        crew_orchestrator = CrewOrchestrator(
            db_service=db_service,
            redis_service=redis_service,
            settings=settings
        )
        await crew_orchestrator.initialize()
        
        # Store services in app state
        app.state.crew_orchestrator = crew_orchestrator
        app.state.db_service = db_service
        app.state.redis_service = redis_service
        
        logger.info("WriteCrew Backend startup complete")
        yield
        
    except Exception as e:
        logger.error("Failed to start WriteCrew Backend", error=str(e))
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down WriteCrew Backend")
        
        if crew_orchestrator:
            await crew_orchestrator.shutdown()
        
        if redis_service:
            await redis_service.disconnect()
        
        if db_service:
            await db_service.close()
        
        logger.info("WriteCrew Backend shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="WriteCrew Backend",
        description="Multi-agentic AI writing platform with CrewAI integration",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Routes
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(agents.router, prefix="/agents", tags=["agents"])
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail}
            )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    
    return app


# Dependency injection
async def get_crew_orchestrator() -> CrewOrchestrator:
    """Get CrewAI orchestrator instance"""
    return crew_orchestrator


async def get_db_service() -> DatabaseService:
    """Get database service instance"""
    return db_service


async def get_redis_service() -> RedisService:
    """Get Redis service instance"""
    return redis_service


# Create app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WriteCrew Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/info")
async def info(
    crew_orchestrator: CrewOrchestrator = Depends(get_crew_orchestrator)
):
    """Get system information"""
    try:
        agent_stats = await crew_orchestrator.get_agent_statistics()
        
        return {
            "service": "WriteCrew Backend",
            "version": "1.0.0",
            "agents": {
                "total": len(agent_stats),
                "active": sum(1 for stats in agent_stats.values() if stats.get("status") == "active"),
                "available": list(agent_stats.keys())
            },
            "features": [
                "Multi-agent orchestration",
                "Real-time WebSocket communication",
                "4-level permission system",
                "Multi-provider AI integration",
                "Document change tracking"
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system information")


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug
    )

