# app/services/ocr_service.py
"""
OCR Service - STUB VERSION
Actual implementation in app/ai/ocr_engine.py (to be completed)
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service for document text extraction - STUB"""
    
    def __init__(self):
        logger.warning("OCR Service is using STUB implementation")
    
    async def process_cin_front(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        TODO: Implement in app/ai/ocr_engine.py
        This is a placeholder that returns dummy data
        """
        logger.warning("OCR not implemented yet - returning dummy data")
        
        return {
            "extracted_data": {
                "cin_number": "PENDING_OCR",
                "first_name": "NOT_EXTRACTED",
                "last_name": "NOT_EXTRACTED",
                "date_of_birth": None,
                "place_of_birth": None,
                "raw_text": "OCR not implemented",
                "confidence": 0.0
            },
            "validation": {
                "is_valid": False,
                "errors": ["OCR not implemented yet"],
                "warnings": ["Waiting to complete app/ai/ocr_engine.py"],
                "confidence": 0.0
            },
            "raw_ocr_results": []
        }
    
    async def process_cin_back(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        TODO: Implement in app/ai/ocr_engine.py
        """
        logger.warning("OCR not implemented yet - returning dummy data")
        
        return {
            "extracted_data": {
                "address": "NOT_EXTRACTED",
                "expiry_date": None,
                "raw_text": "OCR not implemented",
                "confidence": 0.0
            },
            "raw_ocr_results": []
        }