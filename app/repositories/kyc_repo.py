# app/repositories/kyc_repo.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta

from app.models.kyc_application import KYCApplication, KYCStatus
from app.repositories.base import BaseRepository


class KYCRepository(BaseRepository[KYCApplication]):
    """Repository for KYC applications"""
    
    def __init__(self, db: Session):
        super().__init__(KYCApplication, db)
    
    def get_by_application_number(self, application_number: str) -> Optional[KYCApplication]:
        """Get application by application number"""
        return self.db.query(KYCApplication).filter(
            KYCApplication.application_number == application_number
        ).first()
    
    def get_by_cin(self, cin_number: str) -> Optional[KYCApplication]:
        """Get application by CIN number"""
        return self.db.query(KYCApplication).filter(
            KYCApplication.cin_number == cin_number
        ).order_by(KYCApplication.created_at.desc()).first()
    
    def get_by_customer_id(self, customer_id: str) -> List[KYCApplication]:
        """Get all applications for a customer"""
        return self.db.query(KYCApplication).filter(
            KYCApplication.customer_id == customer_id
        ).order_by(KYCApplication.created_at.desc()).all()
    
    def get_by_status(
        self,
        status: KYCStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[KYCApplication]:
        """Get applications by status"""
        return self.db.query(KYCApplication).filter(
            KYCApplication.status == status
        ).offset(skip).limit(limit).all()
    
    def get_pending_review(
        self,
        agent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[KYCApplication]:
        """Get applications pending manual review"""
        query = self.db.query(KYCApplication).filter(
            KYCApplication.status == KYCStatus.MANUAL_REVIEW
        )
        
        if agent_id:
            query = query.filter(KYCApplication.assigned_agent_id == agent_id)
        
        return query.offset(skip).limit(limit).all()
    
    def count_by_ip(self, ip_address: str, days: int = 7) -> int:
        """Count applications from same IP in last N days"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.db.query(KYCApplication).filter(
            and_(
                KYCApplication.ip_address == ip_address,
                KYCApplication.created_at >= since
            )
        ).count()
    
    def get_expired_applications(self) -> List[KYCApplication]:
        """Get expired applications that need cleanup"""
        return self.db.query(KYCApplication).filter(
            and_(
                KYCApplication.expires_at <= datetime.utcnow(),
                KYCApplication.status.in_([
                    KYCStatus.DRAFT,
                    KYCStatus.SUBMITTED,
                    KYCStatus.DOCUMENT_VERIFICATION
                ])
            )
        ).all()