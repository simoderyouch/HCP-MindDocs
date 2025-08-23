# RAG Backend API

A high-performance Retrieval-Augmented Generation (RAG) backend built with FastAPI, featuring document processing, AI-powered chat, vector search, intelligent caching, and OCR support for scanned documents.

## 🚀 Features

### Core Functionality
- **Document Processing**: Support for PDF, DOCX, PPTX, HTML, CSV, and text files
- **OCR Support**: Automatic text extraction from scanned PDFs and images
- **Vector Search**: Qdrant-based semantic search with embeddings
- **AI Chat**: Context-aware conversations with document knowledge
- **Multi-Document Chat**: Simultaneous chat with multiple documents for comprehensive analysis
- **File Storage**: MinIO object storage for document management
- **User Authentication**: JWT-based secure authentication

### Performance & Reliability
- **Message Caching**: Redis-based caching for faster chat history retrieval
- **Database Optimization**: PostgreSQL with connection pooling and indexing
- **Structured Logging**: JSON-formatted logs with rotation and context
- **Error Handling**: Centralized exception handling with detailed error responses
- **Health Monitoring**: Comprehensive health checks and metrics
- **Performance Tracking**: Request timing and system resource monitoring
- **Token Management**: Intelligent token limiting for large documents

### Architecture
- **Microservices**: Docker Compose orchestration
- **Scalable**: Horizontal scaling ready
- **Production-Ready**: Security middleware, CORS, and HTTPS support
- **Monitoring**: Real-time metrics and health endpoints

## 💬 Multi-Document Chat

### Multi-Document Analysis
The system supports simultaneous chat with multiple documents, allowing users to ask questions that span across multiple files and get comprehensive answers that synthesize information from all relevant sources.

### Multi-Document Features
- **Cross-Document Analysis**: Ask questions that require information from multiple documents
- **Information Synthesis**: AI automatically combines and synthesizes information from different sources
- **Source Attribution**: Responses clearly indicate which document(s) the information comes from
- **Conflict Resolution**: When information conflicts between documents, the AI acknowledges and explains differences
- **Comprehensive Context**: Reduced token limits per document to accommodate multiple sources

### Multi-Document API Usage
```bash
# Chat with multiple documents
curl -X POST "http://localhost:8000/api/chat/multi-document" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare the policies in document A and document B",
    "file_ids": [1, 2, 3],
    "model": "default",
    "language": "English"
  }'

# Get multi-document chat history
curl -X GET "http://localhost:8000/api/chat/multi-document/messages?file_ids=1&file_ids=2&file_ids=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Multi-Document Response Format
```json
{
  "message": "Based on the analysis of multiple documents...",
  "create_at": "2025-08-14T15:30:00",
  "processing_time": "2.45s",
  "documents_used": [
    {"id": 1, "name": "document1.pdf"},
    {"id": 2, "name": "document2.pdf"},
    {"id": 3, "name": "document3.pdf"}
  ]
}
```

## 🔍 OCR (Optical Character Recognition)

### Automatic OCR Processing
The system automatically detects when standard text extraction fails (produces 0 content) and switches to OCR processing for PDF documents.

### OCR Features
- **Multi-Engine Support**: EasyOCR (primary) and Tesseract (fallback)
- **Multi-Language**: English and French text recognition
- **Image Preprocessing**: Automatic image enhancement for better accuracy
- **Page-by-Page Processing**: Maintains page numbers and document structure
- **Error Recovery**: Graceful fallback between OCR engines

### OCR Configuration
```env
# OCR is automatically enabled when text extraction fails
# No additional configuration required
```

### Supported File Types
- **PDF Documents**: Scanned PDFs, image-based PDFs
- **Image Files**: PNG, JPG, JPEG (via PDF conversion)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd backend
```

### 2. Environment Setup
Create a `.env` file in the backend directory:
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hcp

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=
CACHE_TTL_MESSAGES=1800

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# MinIO Configuration
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=documents

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# AI Model Configuration
MODEL_NAME=your-model-name
API_KEY=your-api-key
```

### 3. Install Dependencies
```bash
# Install Python dependencies (including OCR libraries)
pip install -r requirements

# For Windows users (if PyMuPDF compilation fails)
# Use the Windows-compatible requirements
pip install -r requirements-windows.txt
```

### 4. Start Services
```bash
# Start all services (PostgreSQL, Redis, Qdrant, MinIO)
docker-compose up -d

# Run database migrations (if using Alembic)
alembic upgrade head
```

### 5. Start the Application
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token

### Documents
- `POST /api/document/upload` - Upload and process documents (with OCR support)
- `GET /api/document/files` - List user's documents
- `DELETE /api/document/{file_id}` - Delete document

### Chat
- `POST /api/chat/{file_id}` - Chat with document
- `GET /api/chat/messages/{file_id}` - Get chat history
- `POST /api/chat/multi-document` - Chat with multiple documents simultaneously
- `GET /api/chat/multi-document/messages` - Get multi-document chat history

### Health & Monitoring
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed` - Detailed health with metrics
- `GET /api/health/metrics` - System and application metrics
- `GET /api/health/cache` - Cache statistics

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Uploaded Files Table
```sql
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    embedding_path VARCHAR(255),
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chat Table
```sql
CREATE TABLE chat (
    id SERIAL PRIMARY KEY,
    question TEXT,
    response TEXT,
    user_id INTEGER REFERENCES users(id),
    uploaded_file_id INTEGER REFERENCES uploaded_files(id),
    source VARCHAR(100),
    created_at_question TIMESTAMP,
    created_at_response TIMESTAMP
);
```

## 🔄 Message Caching

The system implements intelligent message caching using Redis:

### Features
- **Fast Retrieval**: Cached messages return in ~1ms vs ~50ms from database
- **Automatic Invalidation**: Cache cleared when new messages are added
- **Memory Efficient**: 30-minute TTL with LRU eviction
- **Scalable**: Separate Redis database for messages

### Configuration
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
CACHE_TTL_MESSAGES=1800  # 30 minutes
```

### Cache Statistics
```bash
curl http://localhost:8000/api/health/cache
```

## 📊 Monitoring & Health Checks

### Health Endpoints
- **Basic Health**: `GET /api/health/`
- **Detailed Health**: `GET /api/health/detailed`
- **Metrics**: `GET /api/health/metrics`
- **Cache Stats**: `GET /api/health/cache`

### Metrics Collected
- **System**: CPU, Memory, Disk usage
- **Application**: Request times, error rates, throughput
- **Database**: Connection pool stats, query performance
- **Cache**: Hit rates, memory usage, key counts

### Logging
- **Structured JSON logs** with context and request IDs
- **File rotation** with size limits
- **Separate error logs** for debugging
- **Performance logging** for optimization
- **OCR processing logs** with detailed extraction results

## 🐳 Docker Services

### PostgreSQL (Database)
- **Port**: 5432
- **Database**: hcp
- **User**: postgres
- **Password**: postgres
- **Health Check**: Every 30s

### Redis (Caching)
- **Port**: 6379
- **Database**: 1 (for messages)
- **Memory**: 256MB max
- **Persistence**: AOF enabled

### Qdrant (Vector Database)
- **Port**: 6333 (REST), 6334 (gRPC)
- **Storage**: Persistent volume
- **Collections**: Auto-created per document

### MinIO (Object Storage)
- **Port**: 9000 (API), 9001 (Console)
- **User**: minioadmin
- **Password**: minioadmin
- **Bucket**: documents

## 🔒 Security Features

### Authentication & Authorization
- **JWT tokens** with configurable expiration
- **Password hashing** with bcrypt
- **Token refresh** mechanism
- **User session management**

### API Security
- **CORS middleware** with configurable origins
- **Trusted host middleware** for host header protection
- **HTTPS redirect** middleware
- **Input validation** with Pydantic models

### Error Handling
- **Custom exceptions** with detailed error codes
- **Structured error responses** for consistent API
- **Error logging** with context and stack traces
- **Graceful degradation** for service failures

## 🚀 Performance Optimization

### Database Optimization
- **Connection pooling** with SQLAlchemy
- **Database indexes** on frequently queried columns
- **Query optimization** with proper joins
- **Connection monitoring** and health checks

### Caching Strategy
- **Message caching** for chat history
- **Embedding caching** for document processing
- **Response caching** for AI-generated content
- **Cache invalidation** strategies

### Token Management
- **Intelligent token limiting** for large documents
- **Chunked processing** for summaries and questions
- **Token estimation** to prevent API limits
- **Optimized retrieval** with similarity thresholds

### System Optimization
- **Async/await** for I/O operations
- **Background tasks** for heavy processing
- **Memory management** with proper cleanup
- **Resource monitoring** and alerts

## 🧪 Testing

### Run Tests
```bash
# Test message cache
python test_message_cache.py

# Test database connection
python -c "from app.db.database import get_db; next(get_db()).execute('SELECT 1')"

# Test health endpoints
curl http://localhost:8000/api/health/

# Test OCR functionality
python test_ocr_simple.py
```

### Performance Testing
```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/health/

# Cache performance test
python test_message_cache.py
```

## 🔧 Configuration

### Environment Variables
All configuration is centralized in `app/config.py`:

```python
# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hcp")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# AI Models
MODEL_NAME = os.getenv("MODEL_NAME", "default-model")
API_KEY = os.getenv("API_KEY", "")

# MinIO
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "documents")
```

### Logging Configuration
```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Log file paths
LOG_FILE = "logs/app.log"
ERROR_LOG_FILE = "logs/error.log"
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL container
   docker-compose logs postgres
   
   # Test connection
   docker exec -it postgres psql -U postgres -d hcp
   ```

2. **Redis Connection Failed**
   ```bash
   # Check Redis container
   docker-compose logs redis
   
   # Test connection
   docker exec -it redis redis-cli ping
   ```

3. **MinIO Connection Failed**
   ```bash
   # Check MinIO container
   docker-compose logs minio
   
   # Access MinIO console
   http://localhost:9001
   ```

4. **Qdrant Connection Failed**
   ```bash
   # Check Qdrant container
   docker-compose logs qdrant
   
   # Test API
   curl http://localhost:6333/collections
   ```

5. **OCR Processing Issues**
   ```bash
   # Check OCR dependencies
   pip list | grep -E "(easyocr|pytesseract|opencv|pdf2image)"
   
   # Test OCR service
   python -c "from app.services.ocr_service import ocr_service; print('OCR service loaded')"
   
   # Check logs for OCR errors
   tail -f logs/app.log | grep ocr
   ```

### Performance Issues

1. **Slow Response Times**
   - Check cache hit rates: `GET /api/health/cache`
   - Monitor database performance: `GET /api/health/metrics`
   - Review application logs for bottlenecks

2. **High Memory Usage**
   - Monitor Redis memory: `GET /api/health/cache`
   - Check application memory: `GET /api/health/metrics`
   - Review cache TTL settings

3. **Database Connection Issues**
   - Check connection pool stats: `GET /api/health/metrics`
   - Review database configuration
   - Monitor slow queries in logs

4. **OCR Processing Slow**
   - Check system resources during OCR
   - Monitor OCR logs for performance issues
   - Consider reducing DPI for faster processing

### Debugging Features

The system includes comprehensive debugging features:

1. **Document Processing Debug**
   - Automatic detection of empty content
   - Detailed logging of chunking process
   - OCR fallback with detailed error reporting

2. **Token Management Debug**
   - Token estimation logging
   - Chunked processing details
   - API limit monitoring

3. **Error Context**
   - Structured error responses
   - Detailed logging with context
   - Performance tracking for all operations

## 📈 Scaling

### Horizontal Scaling
- **Load Balancer**: Use nginx or HAProxy
- **Multiple Instances**: Run multiple FastAPI workers
- **Database Replication**: PostgreSQL read replicas
- **Redis Cluster**: For high availability

### Vertical Scaling
- **Increase Resources**: More CPU, RAM, Disk
- **Optimize Queries**: Database query optimization
- **Cache Strategy**: Implement multi-level caching
- **Background Processing**: Use Celery for heavy tasks

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8000/docs)
- [Performance Guide](PERFORMANCE.md)

### Issues
- **Bug Reports**: Create an issue with detailed steps
- **Feature Requests**: Use the issue template
- **Questions**: Use discussions or create an issue

### Contact
- **Email**: your-email@example.com
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Built with ❤️ using FastAPI, PostgreSQL, Redis, Qdrant, MinIO, and OCR**
