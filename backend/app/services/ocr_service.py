import os
import tempfile
import cv2
import numpy as np
from PIL import Image
import easyocr
import pytesseract
from pdf2image import convert_from_path
import pypdf
from typing import List, Dict, Any
from app.utils.logger import log_info, log_error, log_warning


class OCRService:
    def __init__(self):
        self.reader = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize OCR engines"""
        try:
            # Try to initialize EasyOCR first (more accurate)
            # Use compatible language combinations
            self.reader = easyocr.Reader(['en', 'fr'])  # Remove Arabic for compatibility
            log_info("EasyOCR initialized successfully", context="ocr_service")
        except Exception as e:
            log_warning(f"EasyOCR initialization failed: {e}, falling back to Tesseract", context="ocr_service")
            self.reader = None
    
    def is_image_based_pdf(self, pdf_path: str) -> bool:
        """Check if PDF is image-based (scanned)"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():  # If any page has text, it's not fully image-based
                        return False
                
                return True  # No text found, likely image-based
        except Exception as e:
            log_error(f"Error checking PDF type: {e}", context="ocr_service")
            return True  # Assume image-based if check fails
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF using OCR"""
        try:
            log_info(f"Starting OCR extraction from PDF: {pdf_path}", context="ocr_service")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            log_info(f"Converted PDF to {len(images)} images", context="ocr_service")
            
            results = []
            for page_num, image in enumerate(images):
                try:
                    # Convert PIL image to OpenCV format
                    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    
                    # Preprocess image for better OCR
                    processed_image = self._preprocess_image(opencv_image)
                    
                    # Extract text using OCR
                    text = self._extract_text_from_image(processed_image)
                    
                    if text.strip():
                        results.append({
                            "page": page_num + 1,
                            "text": text,
                            "extraction_method": "ocr",
                            "text_length": len(text)
                        })
                        
                        log_info(
                            f"Extracted text from page {page_num + 1}",
                            context="ocr_service",
                            page=page_num + 1,
                            text_length=len(text)
                        )
                    else:
                        log_warning(
                            f"No text extracted from page {page_num + 1}",
                            context="ocr_service",
                            page=page_num + 1
                        )
                        
                except Exception as page_error:
                    log_error(
                        f"Error processing page {page_num + 1}: {page_error}",
                        context="ocr_service",
                        page=page_num + 1
                    )
            
            log_info(
                f"OCR extraction completed",
                context="ocr_service",
                total_pages=len(images),
                pages_with_text=len(results)
            )
            
            return results
            
        except Exception as e:
            log_error(f"OCR extraction failed: {e}", context="ocr_service")
            return []
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            log_warning(f"Image preprocessing failed: {e}, using original image", context="ocr_service")
            return image
    
    def _extract_text_from_image(self, image: np.ndarray) -> str:
        """Extract text from image using available OCR engines"""
        text_results = []
        
        # Try EasyOCR first
        if self.reader:
            try:
                results = self.reader.readtext(image)
                text = ' '.join([result[1] for result in results])
                if text.strip():
                    text_results.append(text)
                    log_info("EasyOCR extraction successful", context="ocr_service")
            except Exception as e:
                log_warning(f"EasyOCR failed: {e}", context="ocr_service")
        
        # Try Tesseract as fallback
        try:
            # Try English first, then French
            tesseract_text = pytesseract.image_to_string(image, lang='eng')
            if not tesseract_text.strip():
                tesseract_text = pytesseract.image_to_string(image, lang='fra')
            
            if tesseract_text.strip():
                text_results.append(tesseract_text)
                log_info("Tesseract extraction successful", context="ocr_service")
        except Exception as e:
            log_warning(f"Tesseract failed: {e}", context="ocr_service")
        
        # Return the best result (longest text)
        if text_results:
            best_text = max(text_results, key=len)
            return best_text.strip()
        else:
            return ""


# Create global OCR service instance
ocr_service = OCRService()
