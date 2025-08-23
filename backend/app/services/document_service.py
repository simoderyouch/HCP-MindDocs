import warnings
import aiohttp
import time
warnings.filterwarnings(
    "ignore", message="langchain is deprecated.", category=DeprecationWarning
)
import os
from fastapi import HTTPException

from langchain_community.document_loaders.csv_loader import CSVLoader
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredHTMLLoader,
    UnstructuredFileLoader,
)
from uuid import uuid4
from langchain.schema import Document

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from fastapi import HTTPException
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from app.config import (tokenizer, encoder)
from langchain_community.vectorstores import Chroma

from langchain_qdrant import Qdrant

# pptxtopdf is Windows-only, removed for Linux compatibility
# from pptxtopdf import convert as convertPPTX

from qdrant_client.http import models
from app.config import encoder, qdrant_client
from app.utils.logger import log_info, log_error, log_warning, log_performance
from app.middleware.error_handler import FileProcessingException



import numpy as np
# Load the Sentence-BERT model




async def get_document(documents):
    start_time = time.time()
    
    # Improved chunking strategy
    text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer=tokenizer,
        chunk_size=1000,      # Smaller, more manageable chunks
        chunk_overlap=200,    # 20% overlap for context continuity
        strip_whitespace=True,
        separators=["\n\n", "\n", ". ", " ", ""]  # Semantic boundaries
    )
    
    try:
        docs = text_splitter.split_documents(documents)
        total_content = sum(len(doc.page_content.strip()) for doc in docs)
        print(docs, total_content)
        
        # DEBUG: Check if content is empty and try OCR for PDFs
        if total_content == 0:
            log_warning(
                "No text content extracted, attempting OCR for PDF documents",
                context="document_chunking",
                num_documents=len(documents)
            )
            
            # Try OCR for PDF documents
            try:
                from app.services.ocr_service import ocr_service
                import tempfile
                import os
               
                # Get the source file path from the first document
                if documents and hasattr(documents[0], 'metadata') and 'source' in documents[0].metadata:
                    source_path = documents[0].metadata['source']
                    
                    # Check if it's a PDF file
                    if source_path.lower().endswith('.pdf'):
                        log_info(
                            "PDF detected, attempting OCR processing",
                            context="document_chunking",
                            source_path=source_path
                        )
                        
                        # Create temporary file for OCR processing
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                            # Download file from MinIO - handle both /minio/ paths and relative paths
                            try:
                                from app.utils.minio import initialize_minio
                                from app.config import MINIO_BUCKET_NAME
                                
                                minio_client = initialize_minio()
                                
                                # Determine bucket and object name
                                if source_path.startswith('/minio/'):
                                    # Full MinIO path
                                    from app.utils.parse_minio_path import parse_minio_path
                                    bucket_name, object_name = parse_minio_path(source_path)
                                else:
                                    # Relative path - use default bucket
                                    bucket_name = MINIO_BUCKET_NAME
                                    object_name = source_path.lstrip('/')  # Remove leading slash if present
                                
                                log_info(
                                    f"Downloading file from MinIO for OCR",
                                    context="document_chunking",
                                    bucket_name=bucket_name,
                                    object_name=object_name
                                )
                                
                                # Download file to temporary location
                                response = minio_client.get_object(bucket_name, object_name)
                                temp_file.write(response.read())
                                temp_file_path = temp_file.name
                                
                                log_info(
                                    f"File downloaded successfully for OCR",
                                    context="document_chunking",
                                    temp_file_path=temp_file_path
                                )
                                
                            except Exception as minio_error:
                                log_error(
                                    f"Failed to download file from MinIO: {minio_error}",
                                    context="document_chunking",
                                    source_path=source_path
                                )
                                # Try as local file path as fallback
                                temp_file_path = source_path
                        
                        # Process with OCR
                        ocr_pages = ocr_service.extract_text_from_pdf(temp_file_path)
                        
                        # Convert OCR results to LangChain Document objects
                        ocr_documents = []
                        for page_data in ocr_pages:
                            if page_data["text"].strip():  # Only include pages with text
                                doc = Document(
                                    page_content=page_data["text"],
                                    metadata={
                                        "source": source_path,
                                        "page": page_data["page"],
                                        "extraction_method": "ocr",
                                        "text_length": page_data["text_length"]
                                    }
                                )
                                ocr_documents.append(doc)
                        
                        if ocr_documents:
                            # Split OCR documents
                            docs = text_splitter.split_documents(ocr_documents)
                            total_content = sum(len(doc.page_content.strip()) for doc in docs)
                            
                            log_info(
                                f"OCR processing successful",
                                context="document_chunking",
                                pages_processed=len(ocr_pages),
                                documents_created=len(ocr_documents),
                                chunks_created=len(docs),
                                total_content=total_content
                            )
                        else:
                            log_error(
                                "OCR processing produced no text content",
                                context="document_chunking",
                                source_path=source_path,
                                pages_processed=len(ocr_pages)
                            )
                        
                        # Clean up temporary file
                        if os.path.exists(temp_file_path) and temp_file_path != source_path:
                            try:
                                os.unlink(temp_file_path)
                                log_info(
                                    f"Temporary file cleaned up",
                                    context="document_chunking",
                                    temp_file_path=temp_file_path
                                )
                            except Exception as cleanup_error:
                                log_warning(
                                    f"Failed to clean up temporary file: {cleanup_error}",
                                    context="document_chunking",
                                    temp_file_path=temp_file_path
                                )
                            
                    else:
                        log_warning(
                            "Non-PDF file with no content, OCR not applicable",
                            context="document_chunking",
                            source_path=source_path
                        )
                else:
                    log_warning(
                        "No source path available for OCR processing",
                        context="document_chunking"
                    )
                    
            except ImportError:
                log_error(
                    "OCR service not available - please install OCR dependencies",
                    context="document_chunking"
                )
            except Exception as ocr_error:
                log_error(
                    f"OCR processing failed: {str(ocr_error)}",
                    context="document_chunking"
                )
        
        log_info(
            f"Document chunking completed",
            context="document_chunking",
            total_content=total_content,
            num_chunks=len(docs)
        )
        
        duration = time.time() - start_time
        log_performance(
            "Document chunking completed",
            duration,
            num_documents=len(documents),
            num_chunks=len(docs),
            avg_chunk_size=sum(len(doc.page_content) for doc in docs) / len(docs) if docs else 0
        )
        
        return docs
        
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="document_chunking",
            duration=duration,
            num_documents=len(documents)
        )
        raise FileProcessingException(
            f"Failed to chunk documents: {str(e)}",
            {"num_documents": len(documents), "duration": duration}
        )







def create_qdrant_collection(collection_name: str, vector_dim: int):
    try:
        log_info(
            "Creating Qdrant collection",
            context="qdrant_collection",
            collection_name=collection_name,
            vector_dim=vector_dim
        )
        
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim,
                distance=models.Distance.COSINE  
            )
        )
        log_info(
            f"Collection '{collection_name}' created successfully",
            context="qdrant_collection",
            collection_name=collection_name
        )
    except Exception as e:
        if 'already exists' in str(e).lower():
            log_info(
                f"Collection '{collection_name}' already exists",
                context="qdrant_collection",
                collection_name=collection_name
            )
        else:
            log_error(
                e,
                context="qdrant_collection",
                collection_name=collection_name,
                vector_dim=vector_dim
            )
            raise


async def process_document_qdrant(documents, db_path):
    start_time = time.time()
    
    try:
        log_info(
            "Starting document processing with Qdrant",
            context="document_processing",
            num_documents=len(documents)
        )
        
        # Step 1: Chunk the documents
        docs = await get_document(documents)

        # Step 2: Extract text from each document chunk
        texts = [doc.page_content for doc in docs]

        log_info(
            f"Extracted {len(texts)} text chunks",
            context="document_processing",
            num_chunks=len(texts)
        )

        # Step 3: Generate embeddings
        embeddings = encoder.embed_documents(texts)
        embeddings = np.array(embeddings)
        log_info(
            f"Generated embeddings for {len(embeddings)} chunks",
            context="document_processing",
            embedding_dim=embeddings.shape[1]
        )

        # Step 4: Get or generate a collection name
        file_name = "default_collection"
        
        # DEBUG: Check if docs has content before accessing metadata
        debug_has_docs = True
        

        if docs and "source" in docs[0].metadata:
            file_name = docs[0].metadata["source"].split("/")[-1].split(".")[0]

        # Step 5: Create or validate collection in Qdrant
        create_qdrant_collection(collection_name=file_name, vector_dim=embeddings.shape[1])

        # Step 6: Upload documents and embeddings to Qdrant
        payloads = []
        for text, doc in zip(texts, docs):
            metadata = doc.metadata.copy()
            page_number = metadata.get("page", 0)
            payload = {
                "text": text,
                "page": page_number,
                **metadata
            }
            payloads.append(payload)
            
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=vector.tolist(),
                payload=payload
            )
            for vector, payload in zip(embeddings, payloads)
        ]

        qdrant_client.upsert(
            collection_name=file_name,
            points=points
        )
        
        duration = time.time() - start_time
        log_performance(
            "Document processing with Qdrant completed",
            duration,
            collection_name=file_name,
            points_inserted=len(points)
        )
        
        return {"collection": file_name, "points_inserted": len(points)}
        
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="document_processing",
            duration=duration,
            num_documents=len(documents)
        )
        raise e




def retrieved_docs(question, embedding_url, similarity_threshold=0.2, max_tokens=10000): 
    start_time = time.time()
    
    try:
        log_info(
            "Starting document retrieval",
            context="document_retrieval",
            collection_name=embedding_url,
            question_length=len(question),
            similarity_threshold=similarity_threshold,
            max_tokens=max_tokens
        )
        
        qdrant_store = Qdrant(
            client=qdrant_client,
            collection_name=embedding_url,
            embeddings=encoder,
            content_payload_key="text"
        )

        # Step 1: Embed the question manually
        question_vector = encoder.embed_query(question)

        # Step 2: Search manually to access similarity scores
        results = qdrant_client.search(
            collection_name=embedding_url,
            query_vector=question_vector,
            limit=20,  # Increased from 10 to get more relevant results
            with_payload=True,
            with_vectors=False,
            score_threshold=None  
        )

        # Step 3: Check top score (smaller distance = better match)
        if results and results[0].score < similarity_threshold:
            log_info(
                f"Similarity too low ({results[0].score}), fetching limited documents",
                context="document_retrieval",
                collection_name=embedding_url,
                top_score=results[0].score
            )
            
            # Instead of fetching ALL documents, fetch a reasonable amount
            retrieved_docs = []
            scroll_offset = None
            total_tokens = 0
            max_docs = 30  # Limit number of documents

            while len(retrieved_docs) < max_docs:
                scroll_result, scroll_offset = qdrant_client.scroll(
                    collection_name=embedding_url,
                    limit=min(20, max_docs - len(retrieved_docs)),  # Smaller batches
                    with_payload=True,
                    offset=scroll_offset
                )

                batch = []
                for doc in scroll_result:
                    if hasattr(doc, "payload") and doc.payload and "text" in doc.payload:
                        text = doc.payload.get("text", "")
                        # Estimate tokens (roughly 4 characters per token)
                        estimated_tokens = len(text) // 4
                        
                        if total_tokens + estimated_tokens > max_tokens:
                            log_info(
                                f"Token limit reached ({total_tokens}), stopping retrieval",
                                context="document_retrieval",
                                collection_name=embedding_url,
                                total_tokens=total_tokens,
                                max_tokens=max_tokens
                            )
                            break
                        
                        batch.append(Document(
                            page_content=text,
                            metadata=doc.payload or {}
                        ))
                        total_tokens += estimated_tokens
                
                retrieved_docs.extend(batch)

                if scroll_offset is None or total_tokens >= max_tokens:
                    break
        else:
            # Convert result to langchain.Document with token management
            retrieved_docs = []
            total_tokens = 0
            
            for doc in results:
                if doc.payload.get("text", "").strip():
                    text = doc.payload.get("text", "")
                    estimated_tokens = len(text) // 4
                    
                    if total_tokens + estimated_tokens > max_tokens:
                        log_info(
                            f"Token limit reached ({total_tokens}), stopping retrieval",
                            context="document_retrieval",
                            collection_name=embedding_url,
                            total_tokens=total_tokens,
                            max_tokens=max_tokens
                        )
                        break
                    
                    retrieved_docs.append(Document(
                        page_content=text,
                        metadata=doc.payload or {}
                    ))
                    total_tokens += estimated_tokens
            
            log_info(
                f"Retrieved {len(retrieved_docs)} documents with similarity search",
                context="document_retrieval",
                collection_name=embedding_url,
                top_score=results[0].score if results else None,
                total_tokens=total_tokens
            )

    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="document_retrieval",
            collection_name=embedding_url,
            duration=duration
        )
        return f"Error retrieving documents: {str(e)}"

    if not retrieved_docs:
        log_warning(
            "No relevant documents found",
            context="document_retrieval",
            collection_name=embedding_url
        )
        return "No relevant documents found in the database."

    # Sort by page number if present
    retrieved_docs = sorted(
        retrieved_docs,
        key=lambda doc: int(doc.metadata.get("page", 0)) if str(doc.metadata.get("page", "0")).isdigit() else 0
    )
    
    # Calculate final token count
    total_tokens = sum(len(doc.page_content) // 4 for doc in retrieved_docs)
    
    duration = time.time() - start_time
    log_performance(
        "Document retrieval completed",
        duration,
        collection_name=embedding_url,
        documents_retrieved=len(retrieved_docs),
        total_tokens=total_tokens
    )
    
    return retrieved_docs


