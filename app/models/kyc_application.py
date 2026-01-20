# app/models/kyc_application.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.database import Base


class KYCStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENT_VERIFICATION = "document_verification"
    FACE_VERIFICATION = "face_verification"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KYCApplication(Base):
    __tablename__ = "kyc_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer Information (Encrypted)
    customer_id = Column(String(100), nullable=True, index=True)  # External customer ID
    cin_number = Column(String(20), nullable=False, index=True)  # Encrypted
    first_name = Column(String(100), nullable=False)  # Encrypted
    last_name = Column(String(100), nullable=False)  # Encrypted
    date_of_birth = Column(DateTime, nullable=False)  # Encrypted
    place_of_birth = Column(String(255))  # Encrypted
    nationality = Column(String(50), default="MA")
    phone_number = Column(String(20))  # Encrypted
    email = Column(String(255))  # Encrypted
    address = Column(JSON)  # Encrypted full address object
    
    # Workflow
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.DRAFT, nullable=False, index=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Verification Scores
    document_verification_score = Column(Float, nullable=True)
    face_verification_score = Column(Float, nullable=True)
    overall_confidence_score = Column(Float, nullable=True)
    
    # Review
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Decision
    decision_reason = Column(String, nullable=True)
    decision_made_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, default=dict)  # Additional flexible data
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="kyc_application", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="kyc_application", cascade="all, delete-orphan")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], back_populates="kyc_applications")
    audit_logs = relationship("AuditLog", back_populates="kyc_application")

    def __repr__(self):
        return f"<KYCApplication {self.application_number} - {self.status}>"