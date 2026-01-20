# app/services/face_service.py
"""
Face Service - STUB VERSION
Actual implementation in app/ai/face_recognition.py (to be completed)
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class FaceService:
    """Face verification service - STUB"""
    
    def __init__(self):
        self.min_face_size = (100, 100)
        self.match_threshold = 0.90
        logger.warning("Face Service is using STUB implementation")
    
    async def verify_face_match(
        self,
        document_image_bytes: bytes,
        selfie_image_bytes: bytes
    ) -> Dict[str, Any]:
        """
        TODO: Implement in app/ai/face_recognition.py
        This is a placeholder that returns dummy data
        """
        logger.warning("Face verification not implemented yet - returning dummy data")
        
        return {
            "is_match": False,
            "similarity_score": 0.0,
            "threshold": self.match_threshold,
            "quality_checks": {
                "document_face_quality": 0.0,
                "selfie_face_quality": 0.0,
                "lighting_check": False,
                "blur_check": False
            },
            "confidence": 0.0,
            "message": "Face recognition not implemented yet"
        }
    
    async def detect_liveness(self, video_frames: List[bytes]) -> Dict[str, Any]:
        """
        TODO: Implement liveness detection
        """
        logger.warning("Liveness detection not implemented yet")
        
        return {
            "is_live": False,
            "liveness_score": 0.0,
            "checks": {
                "blink_detected": False,
                "movement_detected": False,
                "depth_score": 0.0,
                "texture_score": 0.0
            },
            "message": "Liveness detection not implemented"
        }