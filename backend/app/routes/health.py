from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db, get_db_stats
from app.db.models import User
from app.config import qdrant_client
from app.utils.minio import initialize_minio
from app.middleware.performance import get_performance_summary, get_system_stats
from app.middleware.error_handler import get_request_id
from app.utils.logger import log_info, log_error
import time
import psutil

router = APIRouter()

def check_minio_connection() -> bool:
    """Check if MinIO connection is healthy"""
    try:
        minio_client = initialize_minio()
        minio_client.list_buckets()
        return True
    except Exception as e:
        log_error(e, context="minio_health_check")
        return False

def check_qdrant_connection() -> bool:
    """Check if Qdrant connection is healthy"""
    try:
        qdrant_client.get_collections()
        return True
    except Exception as e:
        log_error(e, context="qdrant_health_check")
        return False

@router.get("/")
async def health_check(request: Request):
    """Basic health check endpoint"""
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        # Check database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Qdrant connection
        qdrant_client.get_collections()
        
        # Check MinIO connection
        minio_client = initialize_minio()
        minio_client.list_buckets()

        
        duration = time.time() - start_time
        
        log_info(
            "Health check completed successfully",
            context="health_check",
            request_id=request_id,
            duration=duration
        )
        
        return JSONResponse(
            status_code=200,
            content={
        "status": "healthy",
                "timestamp": time.time(),
                "request_id": request_id,
                "response_time": f"{duration:.3f}s",
                "services": {
                    "database": "healthy",
                    "qdrant": "healthy",
                    "minio": "healthy",
                }
            }
        )
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="health_check",
            request_id=request_id,
            duration=duration
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "request_id": request_id,
                "response_time": f"{duration:.3f}s",
                "error": str(e)
            }
        )

@router.get("/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with system metrics"""
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        # Basic health checks
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        qdrant_client.get_collections()
        
        minio_client = initialize_minio()
        minio_client.list_buckets()
        
        # Get detailed metrics
        system_stats = get_system_stats()
        performance_summary = get_performance_summary()
        
        duration = time.time() - start_time
        
        log_info(
            "Detailed health check completed",
            context="health_check",
            request_id=request_id,
            duration=duration
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": time.time(),
                "request_id": request_id,
                "response_time": f"{duration:.3f}s",
                "services": {
                    "database": "healthy",
                    "qdrant": "healthy",
                    "minio": "healthy",
                   
                },
                "system": system_stats,
                "performance": performance_summary
            }
        )
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="detailed_health_check",
            request_id=request_id,
            duration=duration
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "request_id": request_id,
                "response_time": f"{duration:.3f}s",
                "error": str(e)
            }
        )

@router.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus-style metrics endpoint"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Database metrics
        db_stats = get_db_stats()
        
        # Application metrics
        process = psutil.Process()
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_used": memory.used
            },
            "database": db_stats,
            "application": {
                "pid": process.pid,
                "memory_rss": process.memory_info().rss,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            }
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        log_error(e, context="metrics")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to collect metrics"}
        )

