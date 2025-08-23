import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import json
import traceback
from typing import Any, Dict, Optional
import os

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_entry)

def setup_logger(name: str = "hcp_backend", log_level: str = "INFO") -> logging.Logger:
    """Setup logger with file rotation and console output"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with JSON formatting and rotation
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / f"{name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    # Error file handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / f"{name}_errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Create main logger instance
logger = setup_logger()

def log_with_context(level: str, message: str, **kwargs) -> None:
    """Log with additional context"""
    extra = {}
    for key, value in kwargs.items():
        if value is not None:
            extra[key] = value
    
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)

def log_error(error: Exception, context: str = "", **kwargs) -> None:
    """Centralized error logging with context"""
    error_msg = f"Error in {context}: {str(error)}"
    log_with_context("ERROR", error_msg, **kwargs)

def log_info(message: str, context: str = "", **kwargs) -> None:
    """Centralized info logging with context"""
    info_msg = f"Info in {context}: {message}"
    log_with_context("INFO", info_msg, **kwargs)

def log_warning(message: str, context: str = "", **kwargs) -> None:
    """Centralized warning logging with context"""
    warning_msg = f"Warning in {context}: {message}"
    log_with_context("WARNING", warning_msg, **kwargs)

def log_debug(message: str, context: str = "", **kwargs) -> None:
    """Centralized debug logging with context"""
    debug_msg = f"Debug in {context}: {message}"
    log_with_context("DEBUG", debug_msg, **kwargs)

def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics"""
    perf_msg = f"Performance: {operation} took {duration:.3f}s"
    log_with_context("INFO", perf_msg, operation=operation, duration=duration, **kwargs)
