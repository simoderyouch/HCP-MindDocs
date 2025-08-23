from fastapi import APIRouter, Depends, HTTPException, Body, Request, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime
from typing import List, Dict, Any
from app.db.models import Chat, UploadedFile
from app.utils.auth import get_current_user
from app.db.database import get_db
from app.services.chat_service import generate_response, generate_multi_document_response
from app.services.document_service import retrieved_docs
from app.middleware.error_handler import ValidationException, DatabaseException, FileProcessingException
from app.middleware.error_handler import get_request_id
from app.utils.logger import log_info, log_error, log_warning, log_performance
import time

router = APIRouter()

async def get_file_messages(file_id: int, user_id: int, db: Session, request_id: str = None, limit: int = 10) -> list:
    try:

        file = db.query(UploadedFile).filter(UploadedFile.owner_id == user_id, UploadedFile.id == file_id).first()
        if file is None:
            log_warning(
                "File not found for message retrieval",
                context="chat_messages",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("File not found", {"file_id": file_id, "user_id": user_id})
            
        # Get only recent messages with limit
        chats = db.query(Chat).filter(
            Chat.uploaded_file_id == file.id
        ).order_by(asc(Chat.created_at_question)).limit(limit).all()
        
        if not chats:
            log_info(
                "No chat messages found for file",
                context="chat_messages",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            return []
        
        messages = []
        for chat in chats:
            if chat.question:
                messages.append({"role": "user", "content": chat.question})
            if chat.response:
                messages.append({"role": "assistant", "content": chat.response})
        
       
                
        log_info(
            f"Retrieved {len(messages)} messages for file (limited to {limit})",
            context="chat_messages",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            message_count=len(messages),
            limit=limit
        )
        return messages
        
    except (ValidationException, DatabaseException):
        raise
    except Exception as e:
        log_error(
            e,
            context="chat_messages",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id
        )
        raise DatabaseException("Failed to retrieve file messages", {"file_id": file_id, "user_id": user_id})

@router.post("/multi-document")
async def chat_with_multiple_documents(
    request: Request,
    question: str = Body(...),
    file_ids: List[int] = Body(...),
    model: str = Body(...),
    language: str = Body(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        log_info(
            "Multi-document chat request started",
            context="multi_document_chat",
            request_id=request_id,
            user_id=user_id,
            question_length=len(question),
            language=language,
            num_files=len(file_ids)
        )
        
        # Validate file IDs and check ownership
        files = []
        for file_id in file_ids:
            file = db.query(UploadedFile).filter(
                UploadedFile.owner_id == user_id, 
                UploadedFile.id == file_id
            ).first()
            
            if file is None:
                log_warning(
                    "File not found for multi-document chat",
                    context="multi_document_chat",
                    request_id=request_id,
                    file_id=file_id,
                    user_id=user_id
                )
                raise ValidationException(f"File not found: {file_id}", {"file_id": file_id, "user_id": user_id})
            
            if file.embedding_path is None:
                log_warning(
                    "File not processed for multi-document chat",
                    context="multi_document_chat",
                    request_id=request_id,
                    file_id=file_id,
                    user_id=user_id
                )
                raise ValidationException(f"File not processed: {file_id}", {"file_id": file_id, "user_id": user_id})
            
            files.append(file)
        
        # Collect contexts from all documents
        all_contexts = []
        document_names = []
        
        for file in files:
            try:
                # Use token-limited retrieval for each document
                context = retrieved_docs(question, file.embedding_path, max_tokens=5000)  # Reduced for multi-doc
                if isinstance(context, list):  # If retrieved_docs returns a list of documents
                    all_contexts.extend(context)
                else:
                    all_contexts.append(context)
                document_names.append(file.file_name.split('.')[0][:15])
                
                log_info(
                    f"Retrieved context from document: {file.file_name}",
                    context="multi_document_chat",
                    request_id=request_id,
                    file_id=file.id,
                    context_length=len(context) if isinstance(context, list) else 1
                )
                
            except Exception as e:
                log_error(
                    e,
                    context="document_context_retrieval",
                    request_id=request_id,
                    file_id=file.id,
                    user_id=user_id
                )
                # Continue with other documents even if one fails
                continue
        
        if not all_contexts:
            log_warning(
                "No contexts retrieved from any documents",
                context="multi_document_chat",
                request_id=request_id,
                user_id=user_id
            )
            raise FileProcessingException("No relevant content found in any documents", {"file_ids": file_ids})
        
        # Generate response using multi-document context
        try:
            response = await generate_multi_document_response(
                document_names=document_names,
                question=question,
                contexts=all_contexts,
                language=language,
                file_ids=file_ids,
                user_id=user_id
            )
            
            log_info(
                "Multi-document AI response generated successfully",
                context="multi_document_chat",
                request_id=request_id,
                user_id=user_id,
                response_length=len(response),
                num_documents=len(document_names)
            )
            
        except Exception as e:
            log_error(
                e,
                context="multi_document_ai_response",
                request_id=request_id,
                user_id=user_id,
                question=question
            )
            raise FileProcessingException(f"Failed to generate multi-document response: {str(e)}", {"file_ids": file_ids})
        
        response_time = datetime.now()
        
        duration = time.time() - start_time
        log_info(
            "Multi-document chat request completed",
            context="multi_document_chat",
            request_id=request_id,
            user_id=user_id,
            duration=duration,
            num_files=len(file_ids)
        )
        
        return {
            "message": response,
            "create_at": response_time.isoformat(),
            "processing_time": f"{duration:.2f}s",
            "documents_used": [{"id": file.id, "name": file.file_name} for file in files]
        }
        
    except (ValidationException, FileProcessingException, DatabaseException):
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="multi_document_chat",
            request_id=request_id,
            user_id=user_id,
            duration=duration
        )
        raise DatabaseException("Multi-document chat request failed", {"duration": duration})


""" @router.get("/multi-document/messages")
async def get_multi_document_messages(
    request: Request,
    file_ids: List[int] = Query(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        log_info(
            "Retrieving multi-document chat messages",
            context="multi_document_messages",
            request_id=request_id,
            user_id=user_id,
            num_files=len(file_ids)
        )
        
        # Validate file IDs and check ownership
        for file_id in file_ids:
            file = db.query(UploadedFile).filter(
                UploadedFile.owner_id == user_id, 
                UploadedFile.id == file_id
            ).first()
            
            if file is None:
                log_warning(
                    "File not found for multi-document messages",
                    context="multi_document_messages",
                    request_id=request_id,
                    file_id=file_id,
                    user_id=user_id
                )
                raise ValidationException(f"File not found: {file_id}", {"file_id": file_id, "user_id": user_id})
        
        # Get all multi-document chat records for the specified files
        chats = db.query(Chat).filter(
            Chat.uploaded_file_id.in_(file_ids),
            Chat.source == 'multi_document'
        ).order_by(asc(Chat.created_at_question)).all()
        
        if not chats:
            log_info(
                "No multi-document chat messages found",
                context="multi_document_messages",
                request_id=request_id,
                user_id=user_id,
                file_ids=file_ids
            )
            return []
        
        # Transform chats to messages format
        transformed_chats = []
        for chat in chats:
            if chat.question and chat.response:
                if chat.created_at_question < chat.created_at_response:
                    transformed_chats.append({
                        "message": chat.question, 
                        "is_user_message": True, 
                        "create_at": chat.created_at_question,
                        "file_id": chat.uploaded_file_id
                    })
                    transformed_chats.append({
                        "message": chat.response, 
                        "is_user_message": False, 
                        "create_at": chat.created_at_response, 
                        "source": chat.source,
                        "file_id": chat.uploaded_file_id
                    })
                else:
                    transformed_chats.append({
                        "message": chat.response, 
                        "is_user_message": False, 
                        "create_at": chat.created_at_response, 
                        "source": chat.source,
                        "file_id": chat.uploaded_file_id
                    })
                    transformed_chats.append({
                        "message": chat.question, 
                        "is_user_message": True, 
                        "create_at": chat.created_at_question,
                        "file_id": chat.uploaded_file_id
                    })
            elif chat.response:
                transformed_chats.append({
                    "message": chat.response, 
                    "is_user_message": False, 
                    "create_at": chat.created_at_response, 
                    "source": chat.source,
                    "file_id": chat.uploaded_file_id
                })
        
        transformed_chats.sort(key=lambda x: x["create_at"])
        
        duration = time.time() - start_time
        log_info(
            f"Retrieved {len(transformed_chats)} multi-document chat messages",
            context="multi_document_messages",
            request_id=request_id,
            user_id=user_id,
            message_count=len(transformed_chats),
            duration=duration
        )
        
        return transformed_chats
        
    except (ValidationException, DatabaseException):
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="multi_document_messages",
            request_id=request_id,
            user_id=user_id,
            duration=duration
        )
        raise DatabaseException("Failed to retrieve multi-document chat messages", {"duration": duration})

 """
@router.post("/{file_id}")
async def chat_with_file(
    request: Request,
    question: str = Body(...), 
    document: int = Body(...), 
    model: str = Body(...), 
    language: str = Body(...),  
    file_id: int = None, 
    user_id: int = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        log_info(
            "Chat request started",
            context="chat_with_file",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            question_length=len(question),
            language=language
        )
        
        question_time = datetime.now()
        file = db.query(UploadedFile).filter(UploadedFile.owner_id == user_id, UploadedFile.id == file_id).first()
        if file is None:
            log_warning(
                "File not found for chat",
                context="chat_with_file",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("File not found", {"file_id": file_id, "user_id": user_id})
        
        if file.embedding_path is None:
            log_warning(
                "File not processed for chat",
                context="chat_with_file",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("Processed document not found", {"file_id": file_id, "user_id": user_id})
        
        message_history = await get_file_messages(file_id, user_id, db, request_id)
        
        try:
            # Use token-limited retrieval to avoid hitting Groq limits
            context = retrieved_docs(question, file.embedding_path, max_tokens=10000)
            response = await generate_response(
                file.file_name.split('.')[0][:15], 
                question, 
                context, 
                memory=message_history, 
                language=language,
                file_id=file_id,
                user_id=user_id
            )
            
            log_info(
                "AI response generated successfully",
                context="chat_with_file",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id,
                response_length=len(response)
            )
            
        except Exception as e:
            log_error(
                e,
                context="ai_response_generation",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id,
                question=question
            )
            raise FileProcessingException(f"Failed to generate response: {str(e)}", {"file_id": file_id})
        
        response_time = datetime.now()
        chat = Chat(
            question=question,
            response=response,
            user_id=user_id,
            uploaded_file_id=file_id,
            source='source',
            created_at_question=question_time,
            created_at_response=response_time
        )
        
        try:
            db.add(chat)
            db.commit()
            
            log_info(
                "Chat record saved to database",
                context="chat_with_file",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            
        except Exception as e:
            db.rollback()
            log_error(
                e,
                context="chat_save",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise DatabaseException("Failed to save chat record", {"file_id": file_id, "user_id": user_id})
        
        duration = time.time() - start_time
        log_info(
            "Chat request completed",
            context="chat_with_file",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            duration=duration
        )
        
        return {
            "message": response, 
            'create_at': response_time,
            "processing_time": f"{duration:.2f}s"
        }
        
    except (ValidationException, FileProcessingException, DatabaseException):
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="chat_with_file",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            duration=duration
        )
        raise DatabaseException("Chat request failed", {"duration": duration})
    
    
@router.get("/messages/{file_id}")
async def messages_of_file(
    request: Request,
    file_id: int, 
    user_id: int = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = get_request_id(request)
    
    try:
        log_info(
            "Retrieving chat messages",
            context="chat_messages",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id
        )
        
        file = db.query(UploadedFile).filter(UploadedFile.owner_id == user_id, UploadedFile.id == file_id).first()
        if file is None:
            log_warning(
                "File not found for message retrieval",
                context="chat_messages",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("File not found", {"file_id": file_id, "user_id": user_id})
        
        chats = db.query(Chat).filter(Chat.uploaded_file_id == file.id).order_by(asc(Chat.created_at_question)).all()
        if chats is None:
            log_warning(
                "No chats found for file",
                context="chat_messages",
                request_id=request_id,
                file_id=file_id,
                user_id=user_id
            )
            raise ValidationException("Chats not found", {"file_id": file_id, "user_id": user_id})
         
        transformed_chats = []
        for chat in chats:
           
            if chat.question and chat.response:
                
                if chat.created_at_question < chat.created_at_response:
                    transformed_chats.append({"message": chat.question, "is_user_message": True, "create_at": chat.created_at_question})
                    transformed_chats.append({"message": chat.response, "is_user_message": False, "create_at": chat.created_at_response, "source": chat.source})
                else:
                    transformed_chats.append({"message": chat.response, "is_user_message": False, "create_at": chat.created_at_response, "source": chat.source})
                    transformed_chats.append({"message": chat.question, "is_user_message": True, "create_at": chat.created_at_question})
            # If only response exists
            elif chat.response:
                transformed_chats.append({"message": chat.response, "is_user_message": False, "create_at": chat.created_at_response, "source": chat.source})
                
        transformed_chats.sort(key=lambda x: x["create_at"])
        
        duration = time.time() - start_time
        log_info(
            f"Retrieved {len(transformed_chats)} chat messages",
            context="chat_messages",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            message_count=len(transformed_chats),
            duration=duration
        )
        
        return transformed_chats
        
    except (ValidationException, DatabaseException):
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="chat_messages",
            request_id=request_id,
            file_id=file_id,
            user_id=user_id,
            duration=duration
        )
        raise DatabaseException("Failed to retrieve chat messages", {"duration": duration})


