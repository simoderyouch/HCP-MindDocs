#!/usr/bin/env python3
"""
Startup script for the RAG API application
"""
import uvicorn

def main():
    """Main function to start the application"""
    print("Starting RAG API...")
    print("Server will run on: http://localhost:8080")
    
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8080,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 