from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import io
import logging

from app.dependencies import get_db, get_current_user, get_ip_address
from app.models.user import User
from app.models.document import DocumentType
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.core.exceptions import KYCException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: UUID = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_ip_address)
):
    """
    Upload document for KYC application
    
    **Supported document types:**
    - cin_front: Front side of Moroccan National ID
    - cin_back: Back side of Moroccan National ID
    - selfie: Selfie photo for face verification
    - liveness_video: Video for liveness detection
    - proof_of_address: Utility bill or similar
    
    **File requirements:**
    - Max size: 10MB
    - Formats: JPEG, PNG, PDF
    """
    
    service = DocumentService(db)
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload document
        document = await service.upload_document(
            application_id=application_id,
            document_type=document_type,
            file_content=file_content,
            filename=file.filename,
            ip_address=ip_address
        )
        
        logger.info(f"Document uploaded: {document.id} - Type: {document_type}")
        
        return {
            "id": str(document.id),
            "document_type": document.document_type,
            "status": document.status,
            "filename": document.file_name,
            "message": "Document uploaded successfully. Processing will begin shortly."
        }
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_info(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document information
    
    Returns metadata about the document including OCR results and quality scores
    """
    
    service = DocumentService(db)
    
    try:
        document_data = await service.get_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        return document_data
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download document file
    
    Returns the original uploaded file. Requires authentication.
    """
    
    service = DocumentService(db)
    
    try:
        # Get document metadata
        document_data = await service.get_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        # Download file
        file_content = await service.download_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={document_data['filename']}"
            }
        )
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reprocess document OCR
    
    Useful if initial processing failed or needs to be re-run with updated models
    """
    
    service = DocumentService(db)
    
    try:
        result = await service.process_document(document_id)
        
        logger.info(f"Document reprocessed: {document_id}")
        
        return {
            "message": "Document reprocessed successfully",
            "result": result
        }
        
    except KYCException as e:
        raise e
    except Exception as e:
        logger.error(f"Error reprocessing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document"
        )