from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel
import logging

from app.dependencies import get_db, get_current_user, require_agent
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationResponse
from app.services.face_service import FaceService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


class FaceVerificationRequest(BaseModel):
    application_id: UUID


class FaceVerificationResponse(BaseModel):
    application_id: str
    is_match: bool
    similarity_score: float
    confidence: float
    quality_checks: dict


@router.post("/face-match", response_model=FaceVerificationResponse)
async def verify_face_match(
    request: FaceVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """
    Perform face verification between document photo and selfie
    
    Compares the face from CIN document with uploaded selfie
    """
    
    face_service = FaceService()
    doc_service = DocumentService(db)
    
    try:
        # Get application documents
        from app.repositories.kyc_repo import KYCRepository
        repo = KYCRepository(db)
        application = repo.get_by_id(request.application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Find CIN front and selfie documents
        cin_front = None
        selfie = None
        
        for doc in application.documents:
            if doc.document_type == "cin_front":
                cin_front = doc
            elif doc.document_type == "selfie":
                selfie = doc
        
        if not cin_front or not selfie:
            raise HTTPException(
                status_code=400,
                detail="Both CIN front and selfie documents required"
            )
        
        # Download documents
        cin_content = await doc_service.download_document(cin_front.id, current_user.id)
        selfie_content = await doc_service.download_document(selfie.id, current_user.id)
        
        # Perform face verification
        result = await face_service.verify_face_match(cin_content, selfie_content)
        
        # Save verification result
        verification = Verification(
            kyc_application_id=request.application_id,
            verification_type="face_match",
            result="pass" if result['is_match'] else "fail",
            confidence_score=result['similarity_score'],
            details=result
        )
        
        db.add(verification)
        
        # Update application
        application.face_verification_score = result['similarity_score']
        db.commit()
        
        logger.info(f"Face verification completed for application {request.application_id}: {result['is_match']}")
        
        return {
            "application_id": str(request.application_id),
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in face verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform face verification"
        )


@router.get("/applications/{application_id}/verifications", response_model=List[VerificationResponse])
async def get_application_verifications(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all verification results for an application
    """
    
    verifications = db.query(Verification).filter(
        Verification.kyc_application_id == application_id
    ).all()
    
    return verifications