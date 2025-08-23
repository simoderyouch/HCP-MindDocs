# New Dependency 
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from sqlalchemy.orm import Session
from app.db.models import User, Base
from app.db.database import SessionLocal, engine

from app.routes.auth import router as auth_router
from app.routes.document import router as document_router
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from fastapi.staticfiles import StaticFiles

# Import middleware
from app.middleware.error_handler import error_handler_middleware
from app.middleware.performance import performance_middleware
from app.utils.logger import log_info, log_error

app = FastAPI(
    title="RAG API",
    description="Retrieval-Augmented Generation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS middleware
from app.config import ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=['*'],
)

# Custom middleware (order matters - add last)
app.middleware("http")(error_handler_middleware)
app.middleware("http")(performance_middleware)

# Include routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(document_router, prefix="/api/document")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(health_router, prefix="/api/health")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    log_info("Application starting up", context="startup")
    try:
        # Initialize database connection
        from app.db.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log_info("Database connection established", context="startup")
        

    except Exception as e:
        log_error(e, context="startup")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    log_info("Application shutting down", context="shutdown")
    try:
        # Close database connections
        from app.db.database import engine
        engine.dispose()
        log_info("Database connections closed", context="shutdown")
    except Exception as e:
        log_error(e, context="shutdown")










    
    
    
    





    

