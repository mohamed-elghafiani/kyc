# app/models/audit_log.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    
    # What
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, APPROVE, etc.
    resource_type = Column(String(50), nullable=False)  # KYC_APPLICATION, DOCUMENT, USER, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    kyc_application_id = Column(UUID(as_uuid=True), ForeignKey("kyc_applications.id"), nullable=True)
    
    # Details
    description = Column(String(500))
    changes = Column(JSON, nullable=True)  # Before/after for updates
    audit_metadata = Column(JSON, default=dict)
    
    # When
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Compliance
    retention_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    kyc_application = relationship("KYCApplication", back_populates="audit_logs")

    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_logs_action', 'action', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type} by {self.username}>"