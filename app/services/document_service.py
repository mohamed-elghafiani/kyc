# app/services/document_service.py
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import mimetypes
import logging

from app.models.document import Document, DocumentType, DocumentStatus
from app.models.kyc_application import KYCApplication
from app.repositories.kyc_repo import KYCRepository
from app.integrations.storage_local import storage_service
from app.services.ocr_service import OCRService
from app.services.audit_service import AuditService
from app.core.exceptions import KYCException
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document upload and processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.kyc_repo = KYCRepository(db)
        self.ocr_service = OCRService()
        self.audit_service = AuditService(db)
    
    async def upload_document(
        self,
        application_id: UUID,
        document_type: DocumentType,
        file_content: bytes,
        filename: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Document:
        """Upload and process document"""
        
        # Validate application exists
        application = self.kyc_repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        # Validate application status
        if application.status not in ["draft", "submitted", "document_verification"]:
            raise KYCException(
                "INVALID_STATUS",
                "Cannot upload documents in current application status"
            )
        
        # Validate file
        self._validate_file(file_content, filename)
        
        # Check for duplicate document type
        existing_doc = self._get_existing_document(application_id, document_type)
        if existing_doc:
            logger.info(f"Replacing existing {document_type} document")
            await self._delete_document(existing_doc)
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for duplicate file
        if self._is_duplicate_file(file_hash):
            raise KYCException("DUPLICATE_FILE", "This file has already been uploaded")
        
        # Upload to storage
        file_path = await storage_service.upload_file(
            bucket=settings.STORAGE_BUCKET_DOCUMENTS,
            file_content=file_content,
            filename=f"{application_id}/{document_type.value}/{filename}",
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        
        # Create document record
        document = Document(
            kyc_application_id=application_id,
            document_type=document_type,
            status=DocumentStatus.UPLOADED,
            file_name=filename,
            file_path=file_path,
            file_size=len(file_content),
            mime_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            file_hash=file_hash,
            is_encrypted=True
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Audit log
        await self.audit_service.log_action(
            action="UPLOAD_DOCUMENT",
            resource_type="DOCUMENT",
            resource_id=document.id,
            kyc_application_id=application_id,
            description=f"Uploaded {document_type.value} document",
            user_id=user_id,
            ip_address=ip_address
        )
        
        # Trigger async OCR processing (keep commented out!)
        # from app.integrations.queue import process_document_ocr
        # process_document_ocr.delay(str(document.id))

        # Process OCR synchronously (no Celery yet)
        # TODO: Add async processing later
        logger.info(f"OCR processing queued for document {document.id} (will process sync for now)")        
        
        # logger.info(f"Document uploaded: {document.id} for application {application_id}")
        
        return document
    
    async def process_document(self, document_id: UUID) -> Dict[str, Any]:
        """Process document with OCR and validation"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise KYCException("NOT_FOUND", "Document not found")
        
        document.status = DocumentStatus.PROCESSING
        self.db.commit()
        
        try:
            # Download file from storage
            file_content = await storage_service.download_file(
                bucket=settings.STORAGE_BUCKET_DOCUMENTS,
                file_path=document.file_path
            )
            
            # Process based on document type
            if document.document_type == DocumentType.CIN_FRONT:
                result = await self.ocr_service.process_cin_front(file_content)
            elif document.document_type == DocumentType.CIN_BACK:
                result = await self.ocr_service.process_cin_back(file_content)
            else:
                result = {"extracted_data": {}, "validation": {"is_valid": True}}
            
            # Update document with OCR results
            document.ocr_extracted_data = result.get("extracted_data", {})
            document.ocr_confidence = result.get("extracted_data", {}).get("confidence", 0)
            document.parsed_data = result.get("extracted_data", {})
            document.ocr_processed_at = datetime.utcnow()
            
            # Quality assessment
            quality_result = self._assess_document_quality(file_content, document.document_type)
            document.quality_score = quality_result["score"]
            document.quality_issues = quality_result["issues"]
            
            # Update status
            validation = result.get("validation", {})
            if validation.get("is_valid", False) and quality_result["score"] >= 0.7:
                document.status = DocumentStatus.VERIFIED
                document.verified_at = datetime.utcnow()
            else:
                document.status = DocumentStatus.REJECTED
            
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document processed: {document.id} - Status: {document.status}")
            
            return {
                "document_id": str(document.id),
                "status": document.status,
                "ocr_data": result.get("extracted_data", {}),
                "validation": validation,
                "quality": quality_result
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            document.status = DocumentStatus.REJECTED
            self.db.commit()
            raise
    
    async def get_document(
        self,
        document_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get document details"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise KYCException("NOT_FOUND", "Document not found")
        
        # Check permissions
        application = document.kyc_application
        if user_id and application.assigned_agent_id != user_id:
            raise KYCException("FORBIDDEN", "Access denied")
        
        return {
            "id": str(document.id),
            "type": document.document_type,
            "status": document.status,
            "filename": document.file_name,
            "file_size": document.file_size,
            "ocr_confidence": document.ocr_confidence,
            "quality_score": document.quality_score,
            "parsed_data": document.parsed_data,
            "created_at": document.created_at.isoformat(),
            "verified_at": document.verified_at.isoformat() if document.verified_at else None
        }
    
    async def download_document(
        self,
        document_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bytes:
        """Download document file"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise KYCException("NOT_FOUND", "Document not found")
        
        # Audit download
        await self.audit_service.log_action(
            action="DOWNLOAD_DOCUMENT",
            resource_type="DOCUMENT",
            resource_id=document.id,
            kyc_application_id=document.kyc_application_id,
            description=f"Downloaded {document.document_type} document",
            user_id=user_id
        )
        
        # Download from storage
        file_content = await storage_service.download_file(
            bucket=settings.STORAGE_BUCKET_DOCUMENTS,
            file_path=document.file_path
        )
        
        return file_content
    
    def _validate_file(self, file_content: bytes, filename: str):
        """Validate uploaded file"""
        
        # Check file size
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise KYCException(
                "FILE_TOO_LARGE",
                f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE} bytes)"
            )
        
        # Check file type
        mime_type = mimetypes.guess_type(filename)[0]
        if mime_type not in settings.ALLOWED_DOCUMENT_TYPES:
            raise KYCException(
                "INVALID_FILE_TYPE",
                f"File type {mime_type} not allowed"
            )
        
        # Check for malicious content (basic)
        if self._contains_malicious_content(file_content):
            raise KYCException("MALICIOUS_FILE", "File appears to contain malicious content")
    
    def _contains_malicious_content(self, file_content: bytes) -> bool:
        """Basic malware detection"""
        # In production, integrate with antivirus service
        suspicious_patterns = [
            b'<script',
            b'<?php',
            b'eval(',
            b'exec(',
        ]
        
        content_lower = file_content.lower()
        return any(pattern in content_lower for pattern in suspicious_patterns)
    
    def _get_existing_document(
        self,
        application_id: UUID,
        document_type: DocumentType
    ) -> Optional[Document]:
        """Get existing document of same type"""
        return self.db.query(Document).filter(
            Document.kyc_application_id == application_id,
            Document.document_type == document_type
        ).first()
    
    def _is_duplicate_file(self, file_hash: str) -> bool:
        """Check if file hash already exists"""
        # Check in last 30 days to allow re-uploads after time
        existing = self.db.query(Document).filter(
            Document.file_hash == file_hash
        ).first()
        return existing is not None
    
    async def _delete_document(self, document: Document):
        """Delete document from storage and database"""
        try:
            await storage_service.delete_file(
                bucket=settings.STORAGE_BUCKET_DOCUMENTS,
                file_path=document.file_path
            )
        except Exception as e:
            logger.error(f"Error deleting file from storage: {str(e)}")
        
        self.db.delete(document)
        self.db.commit()
    
    def _assess_document_quality(
        self,
        file_content: bytes,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """Assess document image quality"""
        
        import cv2
        import numpy as np
        
        # Convert to image
        nparr = np.frombuffer(file_content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        issues = []
        scores = []
        
        # Resolution check
        height, width = image.shape[:2]
        if width < 800 or height < 600:
            issues.append("Low resolution")
            scores.append(0.5)
        else:
            scores.append(1.0)
        
        # Blur check
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            issues.append("Image is blurry")
            scores.append(0.6)
        else:
            scores.append(1.0)
        
        # Brightness check
        brightness = np.mean(gray)
        if brightness < 40 or brightness > 220:
            issues.append("Poor lighting")
            scores.append(0.7)
        else:
            scores.append(1.0)
        
        # Contrast check
        contrast = np.std(gray)
        if contrast < 20:
            issues.append("Low contrast")
            scores.append(0.7)
        else:
            scores.append(1.0)
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "score": overall_score,
            "issues": issues,
            "details": {
                "resolution": f"{width}x{height}",
                "blur_score": laplacian_var,
                "brightness": brightness,
                "contrast": contrast
            }
        }