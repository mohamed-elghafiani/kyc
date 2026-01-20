"""
TASK: Implement OCR for Moroccan CIN cards

Requirements:
1. Extract these fields from CIN:
   - CIN Number (e.g., "AB123456")
   - First Name (Arabic + Latin)
   - Last Name (Arabic + Latin)
   - Date of Birth
   - Place of Birth
   - Expiry Date

2. Handle:
   - Low quality images
   - Skewed/rotated images
   - Poor lighting

3. Return confidence score (0-100%)

Example CIN Layout:
┌─────────────────────────────────────┐
│ [Photo]  الاسم: محمد العلمي        │
│          Nom: MOHAMMED ALAMI         │
│          CIN: AB123456               │
│          Date naissance: 15/01/1990  │
└─────────────────────────────────────┘
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CINOCREngine:
    """OCR Engine for Moroccan CIN cards"""
    
    def __init__(self, engine: str = "easyocr"):
        """
        Initialize OCR engine
        
        Args:
            engine: "easyocr", "paddleocr", or "tesseract"
        """
        self.engine = engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """
        TODO: Initialize your chosen OCR engine here
        
        Example for EasyOCR:
            import easyocr
            self.reader = easyocr.Reader(['ar', 'fr', 'en'], gpu=True)
        """
        # YOUR CODE HERE
        pass
    
    def extract_from_cin_front(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from CIN front side
        
        Returns:
            {
                "cin_number": "AB123456",
                "first_name": "Mohammed",
                "last_name": "Alami",
                "date_of_birth": "1990-01-15",
                "place_of_birth": "Casablanca",
                "confidence": 0.95
            }
        """
        
        # Step 1: Preprocess image
        image = self._preprocess_image(image_bytes)
        
        # Step 2: Run OCR
        ocr_result = self._run_ocr(image)
        
        # Step 3: Parse Moroccan CIN format
        parsed_data = self._parse_cin_data(ocr_result)
        
        # Step 4: Validate extracted data
        validated_data = self._validate_cin_data(parsed_data)
        
        return validated_data
    
    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        TODO: Implement image preprocessing
        
        Steps:
        1. Convert to grayscale
        2. Deskew (fix rotation)
        3. Enhance contrast
        4. Denoise
        5. Resize to optimal size
        """
        # YOUR CODE HERE
        pass
    
    def _run_ocr(self, image: np.ndarray) -> list:
        """
        TODO: Run OCR on preprocessed image
        
        Should return list of detected text with coordinates
        """
        # YOUR CODE HERE
        pass
    
    def _parse_cin_data(self, ocr_result: list) -> Dict[str, Any]:
        """
        TODO: Parse OCR results into structured data
        
        Use regex patterns to find:
        - CIN number: [A-Z]{1,2}\d{6,7}
        - Date: DD/MM/YYYY
        - Names: After keywords "Nom:", "الاسم:"
        """
        # YOUR CODE HERE
        pass
    
    def _validate_cin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        TODO: Validate extracted data
        
        Check:
        - CIN number format is correct
        - Date is valid
        - Required fields are present
        """
        # YOUR CODE HERE
        pass


# Global instance
ocr_engine = CINOCREngine()