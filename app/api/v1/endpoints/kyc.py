from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.dependencies import (
    get_db,
    get_current_user,
    get_ip_address,
    get_user_agent,
    require_agent,
    pagination_params
)
from app.models.user import User
from app.schemas.kyc import (
    KYCApplicationCreate,
    KYCApplicationUpdate,
    KYCApplicationResponse,
    KYCApplicationDetail,
    KYCApprovalRequest,
    KYCRejectionRequest,
    KYCListResponse
)
from app.services.kyc_service import KYCService
from app.core.exceptions import KYCException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/applications", response_model=KYCApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_kyc_application(
    data: KYCApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_ip_address),
    user_agent: str = Depends(get_user_agent)
):
    """
    Create a new KYC application
    
    **Public endpoint** - Can be called without authentication for customer-facing flows
    """
    
    service = KYCService(db)
    
    try:
        application = await service.create_application(
            data=data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"KYC application created: {application.application_number}")
        
        return application
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating KYC application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


@router.get("/applications/{application_id}", response_model=KYCApplicationDetail)
async def get_kyc_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get KYC application details
    
    Requires authentication. Users can only view applications they're assigned to (except admins/auditors)
    """
    
    service = KYCService(db)
    
    try:
        application_data = await service.get_application_details(
            application_id=application_id,
            user=current_user
        )
        
        return application_data
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application"
        )


@router.get("/applications", response_model=KYCListResponse)
async def list_kyc_applications(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent),
    pagination: dict = Depends(pagination_params)
):
    """
    List KYC applications with filters
    
    Requires agent role or higher
    """
    
    from app.repositories.kyc_repo import KYCRepository
    
    repo = KYCRepository(db)
    
    # Build filters
    filters = {}
    if status:
        filters['status'] = status
    if risk_level:
        filters['risk_level'] = risk_level
    
    # Get applications
    if status:
        applications = repo.get_by_status(
            status=status,
            skip=pagination['skip'],
            limit=pagination['limit']
        )
    else:
        applications = repo.get_all(
            skip=pagination['skip'],
            limit=pagination['limit']
        )
    
    total = repo.count(filters)
    
    return {
        "total": total,
        "page": pagination['skip'] // pagination['limit'] + 1,
        "page_size": pagination['limit'],
        "applications": applications
    }


@router.post("/applications/{application_id}/submit", response_model=KYCApplicationResponse)
async def submit_kyc_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_ip_address)
):
    """
    Submit KYC application for verification
    
    Moves application from DRAFT to SUBMITTED status and triggers verification workflow
    """
    
    service = KYCService(db)
    
    try:
        application = await service.submit_application(
            application_id=application_id,
            ip_address=ip_address
        )
        
        logger.info(f"Application submitted: {application.application_number}")
        
        return application
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application"
        )


@router.post("/applications/{application_id}/approve", response_model=KYCApplicationResponse)
async def approve_kyc_application(
    application_id: UUID,
    approval_data: KYCApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """
    Approve KYC application
    
    Requires agent role or higher. Finalizes the KYC process.
    """
    
    service = KYCService(db)
    
    try:
        application = await service.approve_application(
            application_id=application_id,
            user=current_user,
            notes=approval_data.notes
        )
        
        logger.info(f"Application approved: {application.application_number} by {current_user.username}")
        
        return application
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error approving application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve application"
        )


@router.post("/applications/{application_id}/reject", response_model=KYCApplicationResponse)
async def reject_kyc_application(
    application_id: UUID,
    rejection_data: KYCRejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """
    Reject KYC application
    
    Requires agent role or higher. Application is marked as rejected with reason.
    """
    
    service = KYCService(db)
    
    try:
        application = await service.reject_application(
            application_id=application_id,
            user=current_user,
            reason=rejection_data.reason,
            notes=rejection_data.notes
        )
        
        logger.info(f"Application rejected: {application.application_number} by {current_user.username}")
        
        return application
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error rejecting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject application"
        )


@router.get("/applications/pending-review", response_model=List[KYCApplicationResponse])
async def get_pending_review_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent),
    pagination: dict = Depends(pagination_params)
):
    """
    Get applications pending manual review
    
    Returns applications assigned to current agent or unassigned (for supervisors/admins)
    """
    
    from app.repositories.kyc_repo import KYCRepository
    
    repo = KYCRepository(db)
    
    # Supervisors and admins see all, agents see only their assignments
    agent_id = None if current_user.role in ["admin", "supervisor"] else current_user.id
    
    applications = repo.get_pending_review(
        agent_id=agent_id,
        skip=pagination['skip'],
        limit=pagination['limit']
    )
    
    return applications