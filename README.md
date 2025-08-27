# HCP MindDocs - AI-Powered Document Analysis Platform

A comprehensive full-stack application that combines document processing, AI-powered chat, and intelligent document analysis using Retrieval-Augmented Generation (RAG) technology. Built with FastAPI backend and React frontend, featuring OCR support, multi-document chat, and advanced vector search capabilities.


[![Watch the demo](https://img.youtube.com/vi/oXHN8-QJCOU/0.jpg)](https://youtu.be/oXHN8-QJCOU)




## 🚀 Features

### 🤖 AI-Powered Document Analysis
- **RAG Technology**: Retrieval-Augmented Generation for context-aware responses
- **Multi-Document Chat**: Simultaneous analysis across multiple documents
- **Intelligent Search**: Semantic vector search with Qdrant
- **Cross-Document Analysis**: Compare and synthesize information from multiple sources
- **Source Attribution**: Clear indication of information sources

### 📄 Document Processing
- **Multi-Format Support**: PDF, DOCX, PPTX, HTML, CSV, TXT files
- **OCR Integration**: Automatic text extraction from scanned documents
- **Multi-Language OCR**: English and French text recognition
- **Document Viewer**: Built-in viewers for various file formats
- **File Management**: Secure storage with MinIO object storage

### 💬 Advanced Chat System
- **Context-Aware Conversations**: AI remembers conversation context
- **Multi-Document Chat**: Ask questions spanning multiple documents
- **Real-time Responses**: Fast, intelligent answers with source citations
- **Chat History**: Persistent conversation history with caching
- **Token Management**: Intelligent handling of large documents

### 🔐 Security & Authentication
- **JWT Authentication**: Secure user authentication
- **User Management**: Registration, login, and session management
- **File Ownership**: Secure document access control
- **CORS Protection**: Cross-origin request security
- **Input Validation**: Comprehensive data validation

### ⚡ Performance & Scalability
- **Database Optimization**: PostgreSQL with connection pooling
- **Vector Search**: High-performance semantic search
- **Background Processing**: Async document processing
- **Health Monitoring**: Comprehensive system monitoring


## 🛠️ Technology Stack

### Frontend
- **React 18**: Modern UI framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication
- **React Hook Form**: Form management
- **Framer Motion**: Animations and transitions
- **Flowbite React**: UI components
- **PDF.js**: PDF document viewing
- **React PDF Viewer**: Advanced PDF functionality

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **Qdrant**: Vector database for semantic search
- **MinIO**: Object storage for documents
- **LangChain**: AI/ML framework
- **EasyOCR/Tesseract**: OCR processing

### AI/ML
- **OpenAI API**: Large language models
- **Groq API**: Fast inference
- **Sentence Transformers**: Text embeddings
- **Transformers**: Hugging Face models

### DevOps & Monitoring
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **Structured Logging**: JSON-formatted logs
- **Health Checks**: System monitoring

## 📦 Installation

### Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/HCP-MindDocs.git
cd HCP-MindDocs
```

### 2. Backend Setup

#### Environment Configuration
```bash
cd backend
cp .env.example .env
```

Edit `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hcp



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

#### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements
```

#### Start Services
```bash
# Start all services (PostgreSQL, Qdrant, MinIO)
docker-compose up -d


# Start the backend server
uvicorn app.main:app --reload --host localhost --port 8080
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## 🚀 Quick Start

### 1. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs

### 2. Create an Account
1. Navigate to the registration page
2. Create a new account with email and password
3. Log in to access the dashboard

### 3. Upload Documents
1. Click "Upload Document" in the dashboard
2. Select your document (PDF, DOCX, PPTX, etc.)
3. Wait for processing to complete
4. View the document in the built-in viewer

### 4. Start Chatting
1. Select a document from your library
2. Click "Chat with Document"
3. Ask questions about the document content
4. Get AI-powered responses with source citations

### 5. Multi-Document Analysis
1. Navigate to "Multi-Document Chat"
2. Select multiple documents
3. Ask questions that span across all selected documents
4. Get comprehensive answers synthesizing information from all sources

## 📚 API Documentation

### Authentication Endpoints
```bash
POST /api/auth/register    # User registration
POST /api/auth/login       # User login
POST /api/auth/refresh     # Refresh access token
```

### Document Management
```bash
POST /api/document/upload  # Upload and process documents
GET /api/document/files    # List user's documents
DELETE /api/document/{id}  # Delete document
```

### Chat Endpoints
```bash
POST /api/chat/{file_id}   # Chat with single document
GET /api/chat/messages/{file_id}  # Get chat history
POST /api/chat/multi-document     # Multi-document chat
GET /api/chat/multi-document/messages  # Multi-doc chat history
```

### Health & Monitoring
```bash
GET /api/health/           # Basic health check
GET /api/health/detailed   # Detailed health with metrics
GET /api/health/metrics    # System and application metrics
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Core Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hcp
SECRET_KEY=your-secret-key

# AI Services
MODEL_NAME=gpt-4
API_KEY=your-openai-key

# Storage
MINIO_BUCKET_NAME=documents
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Performance
MAX_TOKENS_PER_REQUEST=4000
```

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
```

### Docker Services

#### PostgreSQL
- **Port**: 5432
- **Database**: hcp
- **User**: postgres
- **Password**: postgres



#### Qdrant
- **Port**: 6333 (REST), 6334 (gRPC)
- **Storage**: Persistent volume

#### MinIO
- **Port**: 9000 (API), 9001 (Console)
- **User**: minioadmin
- **Password**: minioadmin
- **Bucket**: documents

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Test specific modules
pytest tests/test_auth.py
pytest tests/test_chat.py
pytest tests/test_document.py

# Performance tests
python test_message_cache.py
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Build for production
npm run build
```

### Integration Tests
```bash
# Test API endpoints
curl http://localhost:8000/api/health/

# Test authentication
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'
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

### Logging
- **Structured JSON logs** with context and request IDs
- **File rotation** with size limits
- **Separate error logs** for debugging
- **Performance logging** for optimization
- **OCR processing logs** with detailed extraction results

## 🚨 Troubleshooting

### Common Issues

#### Backend Issues
```bash
# Database connection failed
docker-compose logs postgres

# MinIO connection failed
docker-compose logs minio

# Check application logs
tail -f backend/logs/app.log
```

#### Frontend Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
lsof -i :3000

# Clear browser cache
# Or use incognito mode
```

#### OCR Issues
```bash
# Check OCR dependencies
pip list | grep -E "(easyocr|pytesseract|opencv|pdf2image)"

# Test OCR service
python -c "from app.services.ocr_service import ocr_service; print('OCR service loaded')"

# Check OCR logs
tail -f backend/logs/app.log | grep ocr
```

### Performance Issues

#### Slow Response Times
- Monitor database performance: `GET /api/health/metrics`
- Review application logs for bottlenecks

#### High Memory Usage
- Check application memory: `GET /api/health/metrics`
- Review system resource usage

#### Database Connection Issues
- Check connection pool stats: `GET /api/health/metrics`
- Review database configuration
- Monitor slow queries in logs

## 🔄 Development Workflow

### Code Structure
```
HCP-MindDocs/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   ├── utils/          # Utilities
│   │   └── middleware/     # Custom middleware
│   ├── tests/              # Backend tests
│   ├── requirements        # Python dependencies
│   └── docker-compose.yml  # Service orchestration
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── docs/                   # Documentation
└── README.md              # This file
```

### Development Commands
```bash
# Backend development
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm start

# Database migrations
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Run tests
cd backend && pytest
cd frontend && npm test
```

## 🚀 Deployment

### Production Setup

#### Backend Deployment
```bash
# Build Docker image
docker build -t hcp-backend .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=your-production-db-url \
  -e REDIS_HOST=your-redis-host \
  hcp-backend
```

#### Frontend Deployment
```bash
# Build for production
cd frontend
npm run build

# Serve with nginx or similar
docker run -d \
  -p 80:80 \
  -v $(pwd)/build:/usr/share/nginx/html \
  nginx:alpine
```

#### Docker Compose Production
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
```env
# Security
SECRET_KEY=your-super-secure-production-key
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Database
DATABASE_URL=postgresql://user:pass@host:port/db



# AI Services
API_KEY=your-production-api-key

# Storage
MINIO_SECURE=true
MINIO_ACCESS_KEY=your-minio-key
MINIO_SECRET_KEY=your-minio-secret
```

## 🤝 Contributing

### Development Setup
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest` (backend) and `npm test` (frontend)
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Guidelines
- **Backend**: Follow PEP 8 style guidelines
- **Frontend**: Use ESLint and Prettier
- **Tests**: Add tests for new features
- **Documentation**: Update docs for API changes
- **Commits**: Use conventional commit messages

### Pull Request Process
1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8080/docs)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

### Issues & Questions
- **Bug Reports**: Create an issue with detailed steps
- **Feature Requests**: Use the issue template
- **Questions**: Use discussions or create an issue
- **Security Issues**: Email directly to maintainers

### Community
- **Discussions**: GitHub Discussions
- **Issues**: GitHub Issues
- **Contributing**: See CONTRIBUTING.md

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **React** for the powerful frontend library
- **LangChain** for AI/ML capabilities
- **Qdrant** for vector search functionality
- **MinIO** for object storage
- **OpenAI** and **Groq** for AI services

## 📈 Roadmap

### Upcoming Features
- [ ] **Real-time Collaboration**: Multi-user document editing
- [ ] **Advanced Analytics**: Document usage insights
- [ ] **Mobile App**: React Native mobile application
- [ ] **API Rate Limiting**: Enhanced API protection
- [ ] **Webhook Support**: External integrations
- [ ] **Advanced OCR**: Support for more languages
- [ ] **Document Versioning**: Track document changes
- [ ] **Export Features**: Export chat conversations

### Performance Improvements
- [ ] **CDN Integration**: Faster static asset delivery
- [ ] **Database Sharding**: Horizontal scaling
- [ ] **Microservices**: Service decomposition
- [ ] **Caching Strategy**: Multi-level caching
- [ ] **Load Balancing**: Traffic distribution

---

**Built with ❤️ using FastAPI, React, PostgreSQL, Redis, Qdrant, MinIO, and AI/ML technologies**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/your-username/HCP-MindDocs).


