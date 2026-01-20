# app/models/document.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.database import Base


class DocumentType(str, enum.Enum):
    CIN_FRONT = "cin_front"
    CIN_BACK = "cin_back"
    PASSPORT = "passport"
    SELFIE = "selfie"
    LIVENESS_VIDEO = "liveness_video"
    PROOF_OF_ADDRESS = "proof_of_address"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kyc_application_id = Column(UUID(as_uuid=True), ForeignKey("kyc_applications.id"), nullable=False)
    
    # Document Info
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    
    # Storage
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # S3/MinIO path
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash
    
    # Encryption
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100), nullable=True)
    
    # OCR Results
    ocr_extracted_data = Column(JSON, nullable=True)  # Raw OCR output
    ocr_confidence = Column(Float, nullable=True)
    ocr_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Document Data (Parsed)
    parsed_data = Column(JSON, nullable=True)  # Structured data
    
    # Quality Checks
    quality_score = Column(Float, nullable=True)
    quality_issues = Column(JSON, nullable=True)  # List of detected issues
    
    # Metadata
    document_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    kyc_application = relationship("KYCApplication", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.document_type} - {self.status}>"