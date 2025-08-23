from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
import aiohttp
import os
import shutil
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import requests
from typing import Dict, List
from docx2pdf import convert
# pptxtopdf is Windows-only, using alternative for Linux
# from pptxtopdf import convert as convertPPTX
def convertPPTX(pptx_path, pdf_path):
    """Fallback function for PPTX to PDF conversion on Linux"""
    print(f"PPTX to PDF conversion not available on Linux: {pptx_path} -> {pdf_path}")
    return False
from app.db.database import get_db
from app.db.models import UploadedFile, User, Chat
from app.utils.file_utils import sanitize_filename
from app.utils.converters import PPTtoPDF
from app.utils.auth import get_current_user
from app.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.services.document_service import process_document_qdrant  
from app.utils.minio import initialize_minio 
from app.config import MINIO_BUCKET_NAME
from minio import Minio
from minio.error import S3Error
import io
from app.utils.MinIOPyMuPDFLoader import MinIOPyMuPDFLoader
import json 
from app.utils.parse_minio_path import parse_minio_path
from app.services.chat_service import generate_response, generate_summary, generate_questions
from app.services.document_service import retrieved_docs
from app.middleware.error_handler import FileProcessingException, ValidationException, DatabaseException
from app.middleware.error_handler import get_request_id
from app.utils.logger import log_info, log_error, log_warning, log_performance
import time
from PIL import Image

minio_client = initialize_minio()
router = APIRouter()






@router.get("/process/{file_id}")
async def process_file(
    request: Request,
    file_id: int, 
    user_id: int = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        log_info(
            "Document processing started",
            context="document_process",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id
        )
        
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not uploaded_file:
            log_warning(
                "File not found for processing",
                context="document_process",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("File not found", {"file_id": file_id})
        
        if uploaded_file.file_type.lower() not in ALLOWED_EXTENSIONS:
            log_warning(
                "Unsupported file type for processing",
                context="document_process",
                request_id=request_id,
                file_id=file_id,
                file_type=uploaded_file.file_type
            )
            raise ValidationException("Unsupported file type", {"file_type": uploaded_file.file_type})
        
        if not uploaded_file.file_path or not uploaded_file.file_path.startswith('/minio/'):
            log_warning(
                "Invalid file path format",
                context="document_process",
                request_id=request_id,
                file_id=file_id,
                file_path=uploaded_file.file_path
            )
            raise ValidationException("Invalid file path format", {"file_path": uploaded_file.file_path})
        
        bucket_name, object_name = parse_minio_path(uploaded_file.file_path)

        # Verify object exists in MinIO before downloading
        try:
            minio_client.stat_object(bucket_name, object_name)
            log_info(
                "File found in MinIO storage",
                context="document_process",
                request_id=request_id,
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            log_error(
                e,
                context="minio_storage",
                request_id=request_id,
                bucket_name=bucket_name,
                object_name=object_name
            )
            raise FileProcessingException(f"File not found in storage: {str(e)}", {"bucket": bucket_name, "object": object_name})



        # Load the document
        try:
            loader = MinIOPyMuPDFLoader(minio_client, bucket_name, object_name)
            documents = loader.load()
            log_info(
                "Document loaded successfully",
                context="document_process",
                request_id=request_id,
                num_documents=len(documents)
            )
        except Exception as e:
            log_error(
                e,
                context="document_loading",
                request_id=request_id,
                file_id=file_id
            )
            raise FileProcessingException(f"Failed to load document: {str(e)}", {"file_id": file_id})


        try:
            result = await process_document_qdrant(
                documents, 
                db_path=None
            ) 
            uploaded_file.embedding_path = result["collection"]  
            db.commit()
            log_info(
                "Document processed with Qdrant successfully",
                context="document_process",
                request_id=request_id,
                collection=result["collection"],
                points_inserted=result["points_inserted"]
            )
        except Exception as e:
            log_error(
                e,
                context="qdrant_processing",
                request_id=request_id,
                file_id=file_id
            )
            raise FileProcessingException(f"Failed to process document: {str(e)}", {"file_id": file_id})

        # Generate summary and questions
        try: 
            short_name = uploaded_file.file_name.split('.')[0][:15]
            # Use token-limited retrieval to avoid hitting Groq limits
            context = retrieved_docs("give me please summary for the document", uploaded_file.embedding_path, max_tokens=10000)

            # Check if context is a string (error message) or list of documents
            if isinstance(context, str):
                log_warning(
                    f"Document retrieval returned error: {context}",
                    context="document_process",
                    request_id=request_id,
                    file_id=file_id
                )
                summary = f"Unable to generate summary: {context}"
                questions = [f"Unable to generate questions: {context}"]
            else:
                summary = await generate_summary(short_name, context)
                questions = await generate_questions(short_name, context)
            
            log_info(
                "Summary and questions generated",
                context="document_process",
                request_id=request_id,
                summary_length=len(summary),
                questions_count=len(questions) if isinstance(questions, list) else 0
            )
        
        except Exception as e:
            log_error(
                e,
                context="ai_generation",
                request_id=request_id,
                file_id=file_id
            )
            raise FileProcessingException(f"Failed to generate response: {str(e)}", {"file_id": file_id})

        # Save to database
        try:
            db.add(Chat(
                response=summary,
                user_id=user_id,
                uploaded_file_id=file_id,
                created_at_response=datetime.now()
            ))

            db.add(Chat(
                response=json.dumps(questions),  
                user_id=user_id,
                uploaded_file_id=file_id,
                created_at_response=datetime.now()
            ))

            db.commit()
            log_info(
                "Chat records saved to database",
                context="document_process",
                request_id=request_id,
                user_id=user_id,
                file_id=file_id
            )
        except Exception as e:
            log_error(
                e,
                context="database_save",
                request_id=request_id,
                user_id=user_id,
                file_id=file_id
            )
            raise DatabaseException("Failed to save chat records", {"user_id": user_id, "file_id": file_id})



        duration = time.time() - start_time
        log_performance(
            "Document processing completed",
            duration,
            request_id=request_id,
            file_id=file_id,
            user_id=user_id
        )

        return {
            "message": "File processed and stored in Qdrant successfully",
            "summary": summary, 
            "questions": questions,
            "processing_time": f"{duration:.2f}s"
        }

    except (ValidationException, FileProcessingException, DatabaseException):
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="document_process",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            duration=duration
        )
        raise DatabaseException("Document processing failed", {"duration": duration})






@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    user_id: int = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        
        file_content = await file.read()
        file_size_bytes = len(file_content)
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"
            )


        sanitized_filename = sanitize_filename(file.filename)
        object_name = f"{user_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sanitized_filename}"

        # Convert images to PDF
        if file_extension in ["png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"]:
            try:
                image = Image.open(io.BytesIO(file_content)).convert("RGB")
                pdf_bytes_io = io.BytesIO()
                image.save(pdf_bytes_io, format="PDF")
                file_content = pdf_bytes_io.getvalue()
                file_size_bytes = len(file_content)
                object_name = f"{object_name.rsplit('.', 1)[0]}.pdf"
                file_extension = 'pdf'
            except Exception as img_err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to convert image to PDF: {str(img_err)}"
                )

        # Convert DOCX to PDF
        if file_extension == 'docx':
            pdf_content = io.BytesIO()
            with io.BytesIO(file_content) as docx_file:
                convert(docx_file, pdf_content)
            file_content = pdf_content.getvalue()
            file_size_bytes = len(file_content)  # Update size after conversion
            object_name = f"{object_name.rsplit('.', 1)[0]}.pdf"
            file_extension = 'pdf'

        # Convert Excel to CSV
        elif file_extension in ['xlsx', 'xls']:
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(excel_file)
            csv_content = io.StringIO()
            df.to_csv(csv_content, index=False)
            file_content = csv_content.getvalue().encode('utf-8')
            file_size_bytes = len(file_content)  # Update size after conversion
            object_name = f"{object_name.rsplit('.', 1)[0]}.csv"
            file_extension = 'csv'

        # Upload to MinIO
        try:
            minio_client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                io.BytesIO(file_content),
                length=file_size_bytes
            )
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to MinIO: {str(e)}"
            )

        file_url = f"/minio/{MINIO_BUCKET_NAME}/{object_name}"

        # Save in DB
        db_file = UploadedFile(
            file_name=sanitized_filename,
            file_type=file_extension.upper(),
            file_path=file_url,
            embedding_path=None,
            owner_id=user_id,
            file_size=file_size_bytes,
            upload_date=datetime.utcnow()  
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return {
            "message": "File uploaded successfully",
            "file": {
                "id": db_file.id,
                "name": db_file.file_name,
                "type": db_file.file_type,
                "url": file_url,
                "size": db_file.file_size,
                "upload_date": db_file.upload_date.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )





@router.get("/files", response_model=Dict[str, List[Dict]])
def get_files_for_user(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Initialize dictionary to store files by type
    files_by_type = {}
    
    # Categorize files by type
    for file in user.uploaded_files:
        file_ext = file.file_type.lower()
        if file_ext in ALLOWED_EXTENSIONS:
            # Initialize the file type category if it doesn't exist
            if file_ext not in files_by_type:
                files_by_type[file_ext] = []
            
            files_by_type[file_ext].append({
                'id': file.id,
                'extention': file.file_type, 
                'file_name': file.file_name, 
                'processed': (True if file.embedding_path else False),
                "size": file.file_size,
                "upload_date": file.upload_date.isoformat()
            })

    return files_by_type






@router.get("/file/{file_id}")
def get_file_by_id(file_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.owner_id == user_id, UploadedFile.id == file_id).first()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if the file path starts with /minio/ indicating it's stored in MinIO
    if file.file_path :
        bucket_name, object_name = parse_minio_path(file.file_path)


        
        try:
            # Get presigned URL for the object that will be valid for 1 hour (3600 seconds)
            url = minio_client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(hours=1)
            )
            file.file_path = url
            
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
    
    file.processed = bool(file.embedding_path)
    
    return file






@router.delete("/file/{file_id}")
def delete_file(file_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        file = db.query(UploadedFile).filter(
            UploadedFile.owner_id == user_id,
            UploadedFile.id == file_id
        ).first()
        
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete from MinIO if file path exists and is a MinIO path
        if file.file_path and file.file_path.startswith('/minio/'):
            bucket_name, object_name = parse_minio_path(file.file_path)
            try:
                minio_client.remove_object(bucket_name, object_name)
            except S3Error as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete file from MinIO: {str(e)}"
                )
                
        
        # Delete related messages
        db.query(Chat).filter(Chat.uploaded_file_id == file_id).delete(synchronize_session=False)
        
        # Delete the file record from database
        db.delete(file)
        db.commit()
        
        return {"message": "File deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

















@router.post("/get_pdf")
async def fetch_pdf(
    url: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):  
    try:
        # Fetch the file from the URL asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # If the response is not successful, raise an error
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail="PDF not found or URL is invalid"
                    )
                
                pdf_data = await response.read()
                content_disposition = response.headers.get('Content-Disposition')
                filename = None

                # Extract filename from the Content-Disposition header if available
                if content_disposition:
                    filename_start = content_disposition.find('filename=') + len('filename=') 
                    filename_end = content_disposition.find(';', filename_start)
                    if filename_end == -1:
                        filename_end = len(content_disposition)
                    filename = content_disposition[filename_start:filename_end].strip('"')
                
                # If filename not found in Content-Disposition, extract it from the URL
                if not filename:
                    filename = url.rsplit('/', 1)[-1]
                
                # Determine the file extension from the filename
                file_extension = filename.split('.')[-1].lower()

                # Check if the file extension is supported
                if file_extension not in ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'webp']:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Unsupported file type. Only PDF, DOC, DOCX, and common image formats are allowed"
                    )

                # Sanitize the filename for storage
                sanitized_filename = sanitize_filename(filename)
                object_name = f"{user_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sanitized_filename}"

                # If image, convert to PDF before upload
                if file_extension in ['png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'webp']:
                    try:
                        image = Image.open(io.BytesIO(pdf_data)).convert("RGB")
                        pdf_buffer = io.BytesIO()
                        image.save(pdf_buffer, format="PDF")
                        pdf_data = pdf_buffer.getvalue()
                        file_extension = 'pdf'
                        sanitized_filename = f"{sanitized_filename.rsplit('.', 1)[0]}.pdf"
                        object_name = f"{object_name.rsplit('.', 1)[0]}.pdf"
                    except Exception as img_err:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Failed to convert image to PDF: {str(img_err)}"
                        )

                # Upload to MinIO
                try:
                    minio_client.put_object(
                        MINIO_BUCKET_NAME,
                        object_name,
                        io.BytesIO(pdf_data),
                        length=len(pdf_data)
                    )
                except S3Error as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload to MinIO: {str(e)}"
                    )

                # Generate file URL
                file_url = f"/minio/{MINIO_BUCKET_NAME}/{object_name}"

                # Save the file info to the database
                db_file = UploadedFile(
                    file_name=sanitized_filename,
                    file_type=file_extension.upper(),
                    file_path=file_url,
                    embedding_path=None,
                    owner_id=user_id
                )
                db.add(db_file)
                db.commit()
                db.refresh(db_file)
            
        return {"message": "File uploaded successfully", 'file': db_file}

    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch the PDF: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )





@router.get("/hcp_files")
async def return_hcp_files(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Read the JSON file instead of querying the database
    json_file_path = os.path.join(os.path.dirname(__file__), 'classeur_data.json')
    
    if not os.path.exists(json_file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="classeur_data.json not found")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        classeur_data = json.load(f)

    # You can further filter or process the data if needed
    return classeur_data

