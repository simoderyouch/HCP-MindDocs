import os
import warnings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from langdetect import detect
from typing import List

from langchain_qdrant import Qdrant

from app.utils.prompt import custom_prompt_template, custom_summary_prompt_template, custom_question_extraction_prompt_template
from app.utils.CustomEmbedding import CustomEmbedding
from app.config import encoder, llm, qdrant_client
from app.utils.logger import log_info, log_error, log_warning, log_performance
import re
import time
warnings.filterwarnings("ignore", message="langchain is deprecated.", category=DeprecationWarning)

from app.services.document_service import retrieved_docs


def clean_response(response: str) -> str:
    """Robust response cleaning that preserves HTML structure and removes thinking tags"""
    try:
        # Always remove thinking tags regardless of case or format
        response_clean = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)
        response_clean = re.sub(r"<thinking>.*?</thinking>", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        response_clean = re.sub(r"<thought>.*?</thought>", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        response_clean = re.sub(r"<reasoning>.*?</reasoning>", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining thinking-related content
        response_clean = re.sub(r"Let me think.*?\.", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        response_clean = re.sub(r"I need to think.*?\.", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        response_clean = re.sub(r"Thinking.*?\.", "", response_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up extra whitespace
        response_clean = re.sub(r'\n\s*\n', '\n\n', response_clean)
        response_clean = response_clean.strip()
        
        # Remove markdown code blocks but preserve HTML
        response_clean = re.sub(r'```.*?```', '', response_clean, flags=re.DOTALL)
        
        # Remove any non-semantic HTML tags that might interfere
        response_clean = re.sub(r'<script.*?</script>', '', response_clean, flags=re.DOTALL)
        response_clean = re.sub(r'<style.*?</style>', '', response_clean, flags=re.DOTALL)
        
        # Ensure proper HTML structure
        if not response_clean.startswith('<article>'):
            # If response doesn't start with article tag, wrap it
            response_clean = f'<article>{response_clean}</article>'
        
        return response_clean.strip()
        
    except Exception as e:
        log_warning(f"Response cleaning failed: {e}")
        return response.strip()

def format_memory_for_prompt(memory: list, max_messages: int = 5) -> str:
    """Format conversation memory for prompt injection"""
    if not memory:
        return "No previous conversation."
    
    # Take only recent messages
    recent_memory = memory[-max_messages:] if len(memory) > max_messages else memory
    
    formatted_memory = []
    for msg in recent_memory:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if content.strip():
            formatted_memory.append(f"{role.title()}: {content}")
    
    return "\n".join(formatted_memory) if formatted_memory else "No previous conversation."

async def generate_response(
    index: str,
    question: str,
    context: list,
    memory: list = None,
    language: str = "Auto-detect",
    file_id: int = None,
    user_id: int = None,
):
    start_time = time.time()
    
    try:
        log_info(
            "Starting AI response generation",
            context="ai_response",
            index=index,
            question_length=len(question),
            context_length=len(context),
            language=language,
            memory_length=len(memory) if memory else 0
        )
        

        
        # Detect language
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(context[0].page_content)
            log_info(
                f"Language detected: {detected_lang}",
                context="ai_response",
                index=index
            )
        except Exception as e:
            detected_lang = "en"
            log_warning(
                "Language detection failed, defaulting to English",
                context="ai_response",
                index=index,
                error=str(e)
            )

        selected_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")

        prompt_template = custom_prompt_template(selected_language)
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Format memory for better prompt injection
        formatted_memory = format_memory_for_prompt(memory or [])

        # Chain: Input → Prompt → LLM → Output
        # Check if LLM is available
        if llm is None:
            log_error(
                "LLM not available - GROQ_API_KEY not configured",
                context="ai_response",
                index=index
            )
            return "AI response generation is not available. Please configure GROQ_API_KEY environment variable."

        rag_chain = (
            {
                "context": lambda _: context,
                "memory": lambda _: formatted_memory,
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        response = rag_chain.invoke(question)
        
        # Use robust response cleaning
        response_clean = clean_response(response)

        duration = time.time() - start_time
        log_performance(
            "AI response generation completed",
            duration,
            index=index,
            response_length=len(response_clean),
            original_length=len(response)
        )

        return response_clean

    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="ai_response",
            index=index,
            question=question,
            duration=duration
        )
        return f"Error: {str(e)}"




async def generate_summary(
    index: str,
    context: List[Document],
    language: str = "Auto-detect",
):
    start_time = time.time()
    
    try:
        log_info(
            "Starting summary generation",
            context="ai_summary",
            index=index,
            context_length=len(context),
            language=language
        )
        
        # Check if context is too large and needs chunking
        total_chars = sum(len(doc.page_content) for doc in context)
        estimated_tokens = total_chars // 4
        
        log_info(
            f"Context token estimation for summary",
            context="ai_summary",
            index=index,
            total_chars=total_chars,
            estimated_tokens=estimated_tokens,
            num_documents=len(context),
            threshold=15000
        )
        
        if estimated_tokens > 15000:
            log_warning(
                f"Context too large ({estimated_tokens} tokens), using chunked processing",
                context="ai_summary",
                index=index,
                estimated_tokens=estimated_tokens
            )
            return await generate_summary_chunked(index, context, language)
        
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(context[0].page_content)
            log_info(
                f"Language detected for summary: {detected_lang}",
                context="ai_summary",
                index=index
            )
        except Exception as e:
            detected_lang = "en"
            log_warning(
                "Language detection failed for summary, defaulting to English",
                context="ai_summary",
                index=index,
                error=str(e)
            )

        selected_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")

        prompt_template = custom_summary_prompt_template(selected_language)
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Check if LLM is available
        if llm is None:
            log_error(
                "LLM not available - GROQ_API_KEY not configured",
                context="ai_summary",
                index=index
            )
            return "AI summary generation is not available. Please configure GROQ_API_KEY environment variable."

        rag_chain = (
            {"context": lambda _: context, "question": lambda _: ""}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        summary = rag_chain.invoke("")
        
        # Clean the response to remove thinking tags
        summary = clean_response(summary)
        
        duration = time.time() - start_time
        log_performance(
            "Summary generation completed",
            duration,
            index=index,
            summary_length=len(summary)
        )
        
        return summary

    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="ai_summary",
            index=index,
            duration=duration
        )
        return f"Error generating summary: {str(e)}"


async def generate_summary_chunked(
    index: str,
    context: List[Document],
    language: str = "Auto-detect",
    chunk_size: int = 10  # Number of documents per chunk
):
    """Generate summary by processing large documents in chunks"""
    try:
        log_info(
            "Starting chunked summary generation",
            context="ai_summary_chunked",
            index=index,
            total_chunks=len(context) // chunk_size + 1
        )
        
        # Split context into chunks
        chunks = [context[i:i + chunk_size] for i in range(0, len(context), chunk_size)]
        
        summaries = []
        for i, chunk in enumerate(chunks):
            log_info(
                f"Processing chunk {i+1}/{len(chunks)}",
                context="ai_summary_chunked",
                index=index,
                chunk_size=len(chunk)
            )
            
            # Generate summary for this chunk
            chunk_summary = await generate_summary_single_chunk(index, chunk, language, i+1, len(chunks))
            summaries.append(chunk_summary)
        
        # Combine summaries if there are multiple chunks
        if len(summaries) > 1:
            log_info(
                "Combining chunk summaries",
                context="ai_summary_chunked",
                index=index,
                num_summaries=len(summaries)
            )
            
            # Create a combined summary
            combined_context = [Document(page_content="\n\n".join(summaries), metadata={"source": "combined_summaries"})]
            final_summary = await generate_summary_single_chunk(index, combined_context, language, 1, 1)
            return final_summary
        else:
            return summaries[0]
            
    except Exception as e:
        log_error(
            e,
            context="ai_summary_chunked",
            index=index
        )
        return f"Error generating chunked summary: {str(e)}"


async def generate_summary_single_chunk(
    index: str,
    context: List[Document],
    language: str,
    chunk_num: int = 1,
    total_chunks: int = 1
):
    """Generate summary for a single chunk of documents"""
    try:
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(context[0].page_content)
        except Exception as e:
            detected_lang = "en"
            log_warning(
                "Language detection failed for chunk summary, defaulting to English",
                context="ai_summary_chunked",
                index=index,
                error=str(e)
            )

        selected_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")

        # Modify prompt for chunked processing
        if total_chunks > 1:
            prompt_template = f"""You are an expert document summarizer. 

Context from part {chunk_num} of {total_chunks} of the document:
{{context}}

Please provide a comprehensive summary of this section of the document in {selected_language}. Focus on the key points, main ideas, and important details.

Summary:"""
        else:
            prompt_template = custom_summary_prompt_template(selected_language)
        
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Check if LLM is available
        if llm is None:
            log_error(
                "LLM not available - GROQ_API_KEY not configured",
                context="ai_summary_single_chunk",
                index=index
            )
            return "AI summary generation is not available. Please configure GROQ_API_KEY environment variable."

        rag_chain = (
            {"context": lambda _: context, "question": lambda _: ""}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        summary = rag_chain.invoke("")
        
        # Clean the response to remove thinking tags
        summary = clean_response(summary)
        
        return summary

    except Exception as e:
        log_error(
            e,
            context="ai_summary_single_chunk",
            index=index,
            chunk_num=chunk_num
        )
        return f"Error generating summary for chunk {chunk_num}: {str(e)}"


import json

async def generate_questions(
    index: str,
    context: List[Document],
    language: str = "Auto-detect",
):
    start_time = time.time()
    
    try:
        log_info(
            "Starting question generation",
            context="ai_questions",
            index=index,
            context_length=len(context),
            language=language
        )
        
        # Check if context is too large and needs chunking
        total_chars = sum(len(doc.page_content) for doc in context)
        estimated_tokens = total_chars // 4
        
        log_info(
            f"Context token estimation for questions",
            context="ai_questions",
            index=index,
            total_chars=total_chars,
            estimated_tokens=estimated_tokens,
            num_documents=len(context),
            threshold=15000
        )
        
        if estimated_tokens > 15000:
            log_warning(
                f"Context too large ({estimated_tokens} tokens), using chunked processing for questions",
                context="ai_questions",
                index=index,
                estimated_tokens=estimated_tokens
            )
            return await generate_questions_chunked(index, context, language)
        
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(context[0].page_content)
            log_info(
                f"Language detected for questions: {detected_lang}",
                context="ai_questions",
                index=index
            )
        except Exception as e:
            detected_lang = "en"
            log_warning(
                "Language detection failed for questions, defaulting to English",
                context="ai_questions",
                index=index,
                error=str(e)
            )

        selected_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")

        prompt_template = custom_question_extraction_prompt_template(selected_language)
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Check if LLM is available
        if llm is None:
            log_error(
                "LLM not available - GROQ_API_KEY not configured",
                context="ai_questions",
                index=index
            )
            return ["AI question generation is not available. Please configure GROQ_API_KEY environment variable."]

        rag_chain = (
            {"context": lambda _: context, "question": lambda _: ""}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        result = rag_chain.invoke("")
        
        # Clean the response to remove thinking tags
        result = clean_response(result)
        
        log_info(
            "Raw question generation result received",
            context="ai_questions",
            index=index,
            result_length=len(result)
        )
        
        match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", result, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
            log_info(
                f"Extracted {len(questions)} questions from JSON",
                context="ai_questions",
                index=index,
                question_count=len(questions)
            )
        else:
            questions = result
            log_warning(
                "Could not extract JSON questions, using raw result",
                context="ai_questions",
                index=index
            )

        duration = time.time() - start_time
        log_performance(
            "Question generation completed",
            duration,
            index=index,
            question_count=len(questions) if isinstance(questions, list) else 0
        )

        return questions
       
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="ai_questions",
            index=index,
            duration=duration
        )
        return f"Error extracting questions: {str(e)}"


async def generate_questions_chunked(
    index: str,
    context: List[Document],
    language: str = "Auto-detect",
    chunk_size: int = 10  # Number of documents per chunk
):
    """Generate questions by processing large documents in chunks"""
    try:
        log_info(
            "Starting chunked question generation",
            context="ai_questions_chunked",
            index=index,
            total_chunks=len(context) // chunk_size + 1
        )
        
        # Split context into chunks
        chunks = [context[i:i + chunk_size] for i in range(0, len(context), chunk_size)]
        
        all_questions = []
        for i, chunk in enumerate(chunks):
            log_info(
                f"Processing chunk {i+1}/{len(chunks)} for questions",
                context="ai_questions_chunked",
                index=index,
                chunk_size=len(chunk)
            )
            
            # Generate questions for this chunk
            chunk_questions = await generate_questions_single_chunk(index, chunk, language, i+1, len(chunks))
            
            # Extract questions from result
            if isinstance(chunk_questions, list):
                all_questions.extend(chunk_questions)
            elif isinstance(chunk_questions, str):
                # Try to extract JSON from string
                match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", chunk_questions, re.DOTALL)
                if match:
                    try:
                        questions = json.loads(match.group(0))
                        all_questions.extend(questions)
                    except:
                        all_questions.append(chunk_questions)
                else:
                    all_questions.append(chunk_questions)
        
        # Remove duplicates and limit to reasonable number
        unique_questions = list(dict.fromkeys(all_questions))  # Preserve order
        final_questions = unique_questions[:10]  # Limit to 10 questions
        
        log_info(
            f"Generated {len(final_questions)} unique questions from chunks",
            context="ai_questions_chunked",
            index=index,
            total_generated=len(all_questions),
            unique_count=len(unique_questions)
        )
        
        return final_questions
            
    except Exception as e:
        log_error(
            e,
            context="ai_questions_chunked",
            index=index
        )
        return f"Error generating chunked questions: {str(e)}"


async def generate_questions_single_chunk(
    index: str,
    context: List[Document],
    language: str,
    chunk_num: int = 1,
    total_chunks: int = 1
):
    """Generate questions for a single chunk of documents"""
    try:
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(context[0].page_content)
        except Exception as e:
            detected_lang = "en"
            log_warning(
                "Language detection failed for chunk questions, defaulting to English",
                context="ai_questions_chunked",
                index=index,
                error=str(e)
            )

        selected_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")

        # Modify prompt for chunked processing
        if total_chunks > 1:
            prompt_template = f"""You are an expert at generating relevant questions from documents.

Context from part {chunk_num} of {total_chunks} of the document:
{{context}}

Please generate 3-5 relevant questions about this section of the document in {selected_language}. Focus on key concepts, important details, and main ideas.

Return the questions as a JSON array of strings, for example: ["Question 1?", "Question 2?", "Question 3?"]

Questions:"""
        else:
            prompt_template = custom_question_extraction_prompt_template(selected_language)
        
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Check if LLM is available
        if llm is None:
            log_error(
                "LLM not available - GROQ_API_KEY not configured",
                context="ai_questions_single_chunk",
                index=index
            )
            return ["AI question generation is not available. Please configure GROQ_API_KEY environment variable."]

        rag_chain = (
            {"context": lambda _: context, "question": lambda _: ""}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        result = rag_chain.invoke("")
        
        # Clean the response to remove thinking tags
        result = clean_response(result)
        
        # Try to extract JSON
        match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", result, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group(0))
                return questions
            except:
                return result
        else:
            return result

    except Exception as e:
        log_error(
            e,
            context="ai_questions_single_chunk",
            index=index,
            chunk_num=chunk_num
        )
        return f"Error generating questions for chunk {chunk_num}: {str(e)}"


async def generate_multi_document_response(
    document_names: List[str],
    question: str,
    contexts: List[Document],
    language: str = "Auto-detect",
    file_ids: List[int] = None,
    user_id: int = None,
):
    start_time = time.time()
    
    try:
        log_info(
            "Starting multi-document AI response generation",
            context="multi_document_ai_response",
            document_names=document_names,
            question_length=len(question),
            context_length=len(contexts),
            language=language,
            num_documents=len(document_names)
        )
        
        # Detect language from context
        language_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        try:
            detected_lang = detect(contexts[0].page_content if contexts else question)
            log_info(
                f"Language detected: {detected_lang}",
                context="multi_document_ai_response",
                document_names=document_names
            )
        except Exception as e:
            log_warning(
                f"Language detection failed: {e}",
                context="multi_document_ai_response",
                document_names=document_names
            )
            detected_lang = "en"
        
        # Use specified language or detected language
        final_language = language if language != "Auto-detect" else language_names.get(detected_lang, "English")
        
        # Format context from multiple documents
        formatted_context = ""
        for i, context in enumerate(contexts):
            if hasattr(context, 'page_content'):
                doc_name = document_names[i] if i < len(document_names) else f"Document {i+1}"
                formatted_context += f"\n\n--- From {doc_name} ---\n{context.page_content}"
            else:
                # Handle case where context might be a string
                doc_name = document_names[i] if i < len(document_names) else f"Document {i+1}"
                formatted_context += f"\n\n--- From {doc_name} ---\n{str(context)}"
        
        # Create multi-document prompt
        multi_doc_prompt = f"""You are an AI assistant analyzing multiple documents. You have access to content from {len(document_names)} different documents.

Documents available: {', '.join(document_names)}

Question: {question}

Context from multiple documents:
{formatted_context}

SYSTEM INSTRUCTIONS:
1. Analyze the question in relation to ALL the provided documents
2. Synthesize information from multiple sources when relevant
3. Clearly indicate which document(s) your information comes from
4. Provide a comprehensive answer that draws from the most relevant documents
5. If information conflicts between documents, acknowledge this and explain the differences
6. Respond in {final_language}

RESPONSE FORMAT REQUIREMENTS:
- Use HTML article format with proper structure
- Include <article> tags as the main container
- Use <h2> for main headings, <h3> for subheadings
- Use <p> for paragraphs with proper spacing
- Use <ul> and <li> for lists when appropriate
- Use <strong> for emphasis on key points
- Use <em> for important terms or concepts
- Include <blockquote> for important quotes or citations
- Use <div> with class="highlight" for key insights
- Ensure proper HTML structure and semantic meaning

Please provide a detailed, well-structured response that addresses the question using information from the relevant documents."""

        # Generate response
        response = llm.invoke(multi_doc_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean the response
        cleaned_response = clean_response(response_text)
        
        duration = time.time() - start_time
        log_performance(
            "Multi-document AI response generation completed",
            duration,
            context="multi_document_ai_response",
            document_names=document_names,
            response_length=len(cleaned_response)
        )
        
        return cleaned_response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error(
            e,
            context="multi_document_ai_response",
            duration=duration,
            document_names=document_names,
            question=question
        )
        raise Exception(f"Failed to generate multi-document response: {str(e)}")