from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.dependencies import get_db, require_auditor, pagination_params
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("/applications/{application_id}/trail", response_model=List[AuditLogResponse])
async def get_application_audit_trail(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor),
    pagination: dict = Depends(pagination_params)
):
    """
    Get complete audit trail for a KYC application
    
    Requires auditor role. Returns all actions performed on the application.
    """
    
    service = AuditService(db)
    
    logs = await service.get_audit_trail(
        kyc_application_id=application_id,
        limit=pagination['limit']
    )
    
    return logs


@router.get("/users/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """
    Get activity logs for a specific user
    
    Requires auditor role. Used for compliance and security monitoring.
    """
    
    service = AuditService(db)
    
    logs = await service.get_user_activity(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return logs