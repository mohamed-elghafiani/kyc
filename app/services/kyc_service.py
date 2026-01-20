#  app/services/kyc_service.py
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.models.kyc_application import KYCApplication, KYCStatus, RiskLevel
from app.models.user import User
from app.repositories.kyc_repo import KYCRepository
from app.schemas.kyc import KYCApplicationCreate, KYCApplicationUpdate
from app.core.security import generate_application_number
from app.core.encryption import encryption, ENCRYPTED_FIELDS
from app.workflows.states import workflow_engine, WorkflowState
from app.services.audit_service import AuditService
from app.core.exceptions import KYCException
from app.config import settings

logger = logging.getLogger(__name__)


class KYCService:
    """Business logic for KYC applications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = KYCRepository(db)
        self.audit_service = AuditService(db)
    
    async def create_application(
        self,
        data: KYCApplicationCreate,
        ip_address: str,
        user_agent: str
    ) -> KYCApplication:
        """Create a new KYC application"""
        
        # Check for duplicate CIN
        existing = self.repo.get_by_cin(data.cin_number)
        if existing and existing.status in [KYCStatus.APPROVED, KYCStatus.SUBMITTED]:
            raise KYCException(
                "DUPLICATE_APPLICATION",
                "An active application already exists for this CIN"
            )
        
        # Generate application number
        application_number = generate_application_number()
        
        # Encrypt sensitive fields
        encrypted_data = self._encrypt_customer_data(data.dict())
        
        # Create application
        application = KYCApplication(
            application_number=application_number,
            status=KYCStatus.DRAFT,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=30),
            **encrypted_data
        )
        
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        
        # Audit log
        await self.audit_service.log_action(
            action="CREATE",
            resource_type="KYC_APPLICATION",
            resource_id=application.id,
            description=f"Created KYC application {application_number}",
            ip_address=ip_address
        )
        
        logger.info(f"Created KYC application: {application_number}")
        return application
    
    async def submit_application(
        self,
        application_id: UUID,
        user: Optional[User] = None,
        ip_address: str = None
    ) -> KYCApplication:
        """Submit application for verification"""
        
        application = self.repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        # Validate application is complete
        validation_result = self._validate_application(application)
        if not validation_result["is_valid"]:
            raise KYCException(
                "INCOMPLETE_APPLICATION",
                f"Application incomplete: {', '.join(validation_result['errors'])}"
            )
        
        # Check workflow transition
        conditions = {
            "has_required_documents": True,
            "has_customer_data": True
        }
        
        can_transition, reason = workflow_engine.can_transition(
            from_state=application.status,
            to_state=WorkflowState.SUBMITTED,
            conditions=conditions,
            user_role="api_client"
        )
        
        if not can_transition:
            raise KYCException("INVALID_TRANSITION", reason)
        
        # Update status
        application.status = KYCStatus.SUBMITTED
        application.submitted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(application)
        
        # Trigger async verification workflow (keep commented out!)
        # from app.integrations.queue import trigger_document_verification
        # trigger_document_verification.delay(str(application.id))

        # Workflow trigger - TODO: Add async processing
        logger.info(f"Application {application.id} ready for next workflow step")
        
        # Audit log
        await self.audit_service.log_action(
            action="SUBMIT",
            resource_type="KYC_APPLICATION",
            resource_id=application.id,
            kyc_application_id=application.id,
            description=f"Submitted application {application.application_number}",
            ip_address=ip_address,
            user_id=user.id if user else None
        )
        
        logger.info(f"Submitted application: {application.application_number}")
        return application
    
    async def approve_application(
        self,
        application_id: UUID,
        user: User,
        notes: Optional[str] = None
    ) -> KYCApplication:
        """Approve KYC application (manual or auto)"""
        
        application = self.repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        # Check permissions
        if user.role not in ["agent", "supervisor", "admin"]:
            raise KYCException("FORBIDDEN", "Insufficient permissions")
        
        # Update application
        application.status = KYCStatus.APPROVED
        application.reviewed_by_id = user.id
        application.review_notes = notes
        application.reviewed_at = datetime.utcnow()
        application.decision_made_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(application)
        
        # Audit log
        await self.audit_service.log_action(
            action="APPROVE",
            resource_type="KYC_APPLICATION",
            resource_id=application.id,
            kyc_application_id=application.id,
            description=f"Approved application {application.application_number}",
            user_id=user.id,
            metadata={"notes": notes}
        )
        
        # Trigger notification (keep commented out!)
        # from app.integrations.queue import send_approval_notification
        # send_approval_notification.delay(str(application.id))

        # Workflow trigger - TODO: Add async processing
        logger.info(f"Application {application.id} ready for next workflow step")
        
        logger.info(f"Approved application: {application.application_number} by {user.username}")
        return application
    
    async def reject_application(
        self,
        application_id: UUID,
        user: User,
        reason: str,
        notes: Optional[str] = None
    ) -> KYCApplication:
        """Reject KYC application"""
        
        application = self.repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        if user.role not in ["agent", "supervisor", "admin"]:
            raise KYCException("FORBIDDEN", "Insufficient permissions")
        
        application.status = KYCStatus.REJECTED
        application.reviewed_by_id = user.id
        application.review_notes = notes
        application.decision_reason = reason
        application.reviewed_at = datetime.utcnow()
        application.decision_made_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(application)
        
        await self.audit_service.log_action(
            action="REJECT",
            resource_type="KYC_APPLICATION",
            resource_id=application.id,
            kyc_application_id=application.id,
            description=f"Rejected application {application.application_number}",
            user_id=user.id,
            metadata={"reason": reason, "notes": notes}
        )
        
        logger.info(f"Rejected application: {application.application_number} by {user.username}")
        return application
    
    async def calculate_risk_score(self, application: KYCApplication) -> float:
        """Calculate overall risk score"""
        
        scores = []
        weights = {
            "document": 0.4,
            "face": 0.4,
            "fraud": 0.2
        }
        
        if application.document_verification_score:
            scores.append(application.document_verification_score * weights["document"])
        
        if application.face_verification_score:
            scores.append(application.face_verification_score * weights["face"])
        
        # Additional fraud checks
        fraud_score = await self._check_fraud_indicators(application)
        scores.append(fraud_score * weights["fraud"])
        
        overall_score = sum(scores) / sum(weights.values()) if scores else 0.0
        
        # Update application
        application.overall_confidence_score = overall_score
        application.risk_level = self._determine_risk_level(overall_score)
        
        self.db.commit()
        
        return overall_score
    
    def _encrypt_customer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive customer data"""
        encrypted = data.copy()
        for field in ENCRYPTED_FIELDS:
            if field in encrypted and encrypted[field]:
                encrypted[field] = encryption.encrypt(str(encrypted[field]))
        return encrypted
    
    def _decrypt_customer_data(self, application: KYCApplication) -> Dict[str, Any]:
        """Decrypt sensitive customer data"""
        data = {}
        for field in ENCRYPTED_FIELDS:
            value = getattr(application, field, None)
            if value:
                data[field] = encryption.decrypt(value)
        return data
    
    def _validate_application(self, application: KYCApplication) -> Dict[str, Any]:
        """Validate application completeness"""
        errors = []
        
        if not application.cin_number:
            errors.append("CIN number required")
        
        if not application.first_name or not application.last_name:
            errors.append("Full name required")
        
        if not application.date_of_birth:
            errors.append("Date of birth required")
        
        # Check for required documents
        required_doc_types = ["cin_front", "cin_back", "selfie"]
        uploaded_types = [doc.document_type for doc in application.documents]
        
        for doc_type in required_doc_types:
            if doc_type not in uploaded_types:
                errors.append(f"Document type {doc_type} required")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level based on confidence score"""
        if score >= 0.9:
            return RiskLevel.LOW
        elif score >= 0.75:
            return RiskLevel.MEDIUM
        elif score >= 0.5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    async def _check_fraud_indicators(self, application: KYCApplication) -> float:
        """Check for fraud indicators"""
        # Implement fraud detection logic
        # - Check for duplicate documents
        # - Check blacklist
        # - Velocity checks (multiple applications same IP/device)
        # - Document tampering detection
        
        fraud_score = 1.0  # Start with clean score
        
        # Example: Check for duplicate submissions
        duplicate_count = self.repo.count_by_ip(application.ip_address)
        if duplicate_count > 5:
            fraud_score -= 0.3
        
        return max(0.0, fraud_score)
    
    async def get_application_details(
        self,
        application_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Get complete application details with decrypted data"""
        
        application = self.repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        # Check permissions
        if user and user.role == "auditor":
            # Auditors can view all
            pass
        elif user and application.assigned_agent_id != user.id:
            raise KYCException("FORBIDDEN", "Not authorized to view this application")
        
        # Decrypt sensitive data
        decrypted_data = self._decrypt_customer_data(application)
        
        # Build response
        response = {
            "id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "customer_data": decrypted_data,
            "documents": [
                {
                    "id": str(doc.id),
                    "type": doc.document_type,
                    "status": doc.status,
                    "confidence": doc.ocr_confidence
                }
                for doc in application.documents
            ],
            "verifications": [
                {
                    "type": ver.verification_type,
                    "result": ver.result,
                    "confidence": ver.confidence_score
                }
                for ver in application.verifications
            ],
            "risk_level": application.risk_level,
            "overall_score": application.overall_confidence_score,
            "created_at": application.created_at.isoformat(),
            "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None
        }
        
        return response