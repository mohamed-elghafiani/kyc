# app/services/audit_service.py
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.audit_log import AuditLog
from app.config import settings

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging and compliance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        kyc_application_id: Optional[UUID] = None,
        description: Optional[str] = None,
        user_id: Optional[UUID] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create audit log entry"""
        
        # Calculate retention period (7 years for compliance)
        retention_until = datetime.utcnow() + timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
        
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            kyc_application_id=kyc_application_id,
            description=description or f"{action} on {resource_type}",
            user_id=user_id,
            username=username,
            ip_address=ip_address or "system",
            user_agent=user_agent,
            changes=changes,
            metadata=metadata or {},
            retention_until=retention_until
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(f"Audit log created: {action} on {resource_type} by {username or 'system'}")
        return audit_log
    
    async def get_audit_trail(
        self,
        kyc_application_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get complete audit trail for an application"""
        
        logs = self.db.query(AuditLog).filter(
            AuditLog.kyc_application_id == kyc_application_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        return logs
    
    async def get_user_activity(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get user activity logs"""
        
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).all()