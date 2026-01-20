# app/schemas/document.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.document import DocumentType, DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    type: DocumentType
    status: DocumentStatus
    filename: str
    file_size: int
    ocr_confidence: Optional[float]
    quality_score: Optional[float]
    parsed_data: Optional[Dict[str, Any]]
    created_at: datetime
    verified_at: Optional[datetime]


class DocumentUploadResponse(BaseModel):
    id: str
    document_type: DocumentType
    status: DocumentStatus
    filename: str
    message: str