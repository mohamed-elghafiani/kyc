# app/models/verification.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.database import Base


class VerificationType(str, enum.Enum):
    DOCUMENT_OCR = "document_ocr"
    FACE_MATCH = "face_match"
    LIVENESS_CHECK = "liveness_check"
    DATA_VALIDATION = "data_validation"
    FRAUD_CHECK = "fraud_check"
    WATCHLIST_SCREENING = "watchlist_screening"


class VerificationResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    MANUAL_REVIEW = "manual_review"
    ERROR = "error"


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kyc_application_id = Column(UUID(as_uuid=True), ForeignKey("kyc_applications.id"), nullable=False)
    
    # Verification Info
    verification_type = Column(SQLEnum(VerificationType), nullable=False)
    result = Column(SQLEnum(VerificationResult), nullable=False)
    
    # Scores
    confidence_score = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    
    # Details
    details = Column(JSON, nullable=True)  # Detailed verification results
    error_message = Column(String, nullable=True)
    
    # Processing
    processing_time_ms = Column(Integer, nullable=True)
    processor = Column(String(100), nullable=True)  # AI model or service used
    
    # Review
    requires_review = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    kyc_application = relationship("KYCApplication", back_populates="verifications")

    def __repr__(self):
        return f"<Verification {self.verification_type} - {self.result}>"