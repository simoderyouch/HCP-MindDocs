import time
import asyncio
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.utils.logger import log_performance, log_warning
from app.db.database import get_db_stats
import psutil
import os

class PerformanceMonitor:
    """Performance monitoring middleware"""
    
    def __init__(self):
        self.request_times = {}
        self.slow_threshold = 2.0  # seconds
        self.critical_threshold = 5.0  # seconds
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Get initial system stats
        initial_cpu = psutil.cpu_percent(interval=None)
        initial_memory = psutil.virtual_memory().percent
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Get final system stats
            final_cpu = psutil.cpu_percent(interval=None)
            final_memory = psutil.virtual_memory().percent
            
            # Log performance metrics
            self._log_performance_metrics(
                request, response, duration, request_id,
                initial_cpu, final_cpu, initial_memory, final_memory
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance(
                f"Request failed after {duration:.3f}s",
                duration,
                request_id=request_id,
                method=request.method,
                endpoint=str(request.url.path),
                error=str(e)
            )
            raise
    
    def _log_performance_metrics(
        self, 
        request: Request, 
        response: Response, 
        duration: float, 
        request_id: str,
        initial_cpu: float,
        final_cpu: float,
        initial_memory: float,
        final_memory: float
    ):
        """Log detailed performance metrics"""
        
        # Basic performance logging
        log_performance(
            f"Request completed",
            duration,
            request_id=request_id,
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            cpu_delta=final_cpu - initial_cpu,
            memory_delta=final_memory - initial_memory
        )
        
        # Warning for slow requests
        if duration > self.critical_threshold:
            log_warning(
                f"Critical slow request: {duration:.3f}s",
                context="performance",
                request_id=request_id,
                method=request.method,
                endpoint=str(request.url.path),
                duration=duration
            )
        elif duration > self.slow_threshold:
            log_warning(
                f"Slow request: {duration:.3f}s",
                context="performance",
                request_id=request_id,
                method=request.method,
                endpoint=str(request.url.path),
                duration=duration
            )

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

async def performance_middleware(request: Request, call_next: Callable) -> Response:
    """Performance monitoring middleware"""
    return await performance_monitor(request, call_next)

def get_system_stats() -> Dict[str, Any]:
    """Get current system statistics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "process": {
                "pid": os.getpid(),
                "memory_info": psutil.Process().memory_info()._asdict(),
                "cpu_percent": psutil.Process().cpu_percent()
            }
        }
    except Exception as e:
        return {"error": str(e)}

def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary including database stats"""
    try:
        db_stats = get_db_stats()
        system_stats = get_system_stats()
        
        return {
            "database": db_stats,
            "system": system_stats,
            "performance_monitor": {
                "slow_threshold": performance_monitor.slow_threshold,
                "critical_threshold": performance_monitor.critical_threshold
            }
        }
    except Exception as e:
        return {"error": str(e)}
