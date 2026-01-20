# app/schemas/verification.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.verification import VerificationType, VerificationResult


class VerificationResponse(BaseModel):
    id: UUID
    verification_type: VerificationType
    result: VerificationResult
    confidence_score: Optional[float]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True