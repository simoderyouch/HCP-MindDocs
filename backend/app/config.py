try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer

from sentence_transformers import SentenceTransformer
from app.utils.CustomEmbedding import CustomEmbedding
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path


from qdrant_client import QdrantClient
import os
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost/hcp")

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "documents")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "1"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Cache Configuration
CACHE_TTL_EMBEDDINGS = int(os.getenv("CACHE_TTL_EMBEDDINGS", "86400"))  # 24 hours
CACHE_TTL_RESPONSES = int(os.getenv("CACHE_TTL_RESPONSES", "3600"))     # 1 hour
CACHE_TTL_DOCUMENTS = int(os.getenv("CACHE_TTL_DOCUMENTS", "7200"))    # 2 hours
CACHE_TTL_CHAT_HISTORY = int(os.getenv("CACHE_TTL_CHAT_HISTORY", "1800"))  # 30 minutes

# AI Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L12-v2")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "multi-qa-MiniLM-L6-cos-v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1-distill-llama-70b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.6"))

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# File Upload Configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/")
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt", "csv", "xls", "xlsx",
    "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"
}
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))


# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://192.168.22.1:3000").split(",")

model = SentenceTransformer(EMBEDDING_MODEL)

encoder = HuggingFaceEmbeddings(
    model_name=MODEL_NAME, 
    model_kwargs={"device": "cpu"}
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)



class Settings(BaseSettings):
    app_name: str = "RAG API"
    admin_email: str = os.getenv("ADMIN_EMAIL", "default@example.com")
    items_per_user: int = int(os.getenv("ITEMS_PER_USER", "50"))
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("Warning: GROQ_API_KEY environment variable not set")
    print("Please set GROQ_API_KEY environment variable to use AI features")
    llm = None
else:
    # Initialize ChatGroq with minimal configuration to avoid compatibility issues
    try:
        # Try with minimal parameters first
        llm = ChatGroq(
            api_key=groq_api_key,
            model_name=LLM_MODEL
        )
        print(f"ChatGroq initialized successfully with model: {LLM_MODEL}")
    except Exception as e:
        print(f"Warning: Could not initialize ChatGroq: {e}")
        print("AI features will be disabled until GROQ_API_KEY is properly configured")
        llm = None