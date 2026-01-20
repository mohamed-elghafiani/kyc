# app/services/workflow_service.py
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.kyc_application import KYCApplication, KYCStatus
from app.models.verification import Verification, VerificationType, VerificationResult
from app.repositories.kyc_repo import KYCRepository
from app.workflows.states import workflow_engine, WorkflowState
from app.services.audit_service import AuditService
from app.core.exceptions import KYCException
from app.config import settings

logger = logging.getLogger(__name__)


class WorkflowService:
    """Manages KYC application workflow and state transitions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = KYCRepository(db)
        self.audit_service = AuditService(db)
    
    async def advance_workflow(
        self,
        application_id: UUID,
        verification_results: Optional[Dict[str, Any]] = None
    ) -> KYCApplication:
        """
        Advance workflow to next state based on verification results
        """
        
        application = self.repo.get_by_id(application_id)
        if not application:
            raise KYCException("NOT_FOUND", "Application not found")
        
        current_state = application.status
        
        # Determine next state based on current state and results
        next_state = self._determine_next_state(application, verification_results)
        
        if next_state == current_state:
            logger.info(f"No state change for application {application_id}")
            return application
        
        # Validate transition
        conditions = self._build_transition_conditions(application, verification_results)
        can_transition, reason = workflow_engine.can_transition(
            from_state=current_state,
            to_state=next_state,
            conditions=conditions,
            user_role="system"
        )
        
        if not can_transition:
            raise KYCException("INVALID_TRANSITION", reason)
        
        # Update application state
        old_status = application.status
        application.status = next_state
        
        # Update scores if provided
        if verification_results:
            self._update_verification_scores(application, verification_results)
        
        self.db.commit()
        self.db.refresh(application)
        
        # Audit log
        await self.audit_service.log_action(
            action="WORKFLOW_TRANSITION",
            resource_type="KYC_APPLICATION",
            resource_id=application.id,
            kyc_application_id=application.id,
            description=f"Workflow transitioned: {old_status} -> {next_state}",
            changes={"old_status": old_status, "new_status": next_state}
        )
        
        # Trigger next workflow step
        await self._trigger_next_step(application, next_state)
        
        logger.info(f"Application {application_id} transitioned: {old_status} -> {next_state}")
        return application
    
    def _determine_next_state(
        self,
        application: KYCApplication,
        verification_results: Optional[Dict[str, Any]]
    ) -> str:
        """Determine next workflow state"""
        
        current = application.status
        
        # State machine logic
        if current == KYCStatus.SUBMITTED:
            return KYCStatus.DOCUMENT_VERIFICATION
        
        elif current == KYCStatus.DOCUMENT_VERIFICATION:
            if verification_results:
                doc_score = verification_results.get("document_verification_score", 0)
                if doc_score >= settings.AUTO_APPROVE_THRESHOLD:
                    return KYCStatus.FACE_VERIFICATION
                elif doc_score >= settings.MANUAL_REVIEW_THRESHOLD:
                    return KYCStatus.FACE_VERIFICATION
                else:
                    return KYCStatus.MANUAL_REVIEW
            return current
        
        elif current == KYCStatus.FACE_VERIFICATION:
            if verification_results:
                face_score = verification_results.get("face_verification_score", 0)
                overall = application.overall_confidence_score or 0
                
                if overall >= settings.AUTO_APPROVE_THRESHOLD:
                    return KYCStatus.APPROVED
                elif overall >= settings.MANUAL_REVIEW_THRESHOLD:
                    return KYCStatus.MANUAL_REVIEW
                else:
                    return KYCStatus.REJECTED
            return current
        
        elif current == KYCStatus.MANUAL_REVIEW:
            # State changes via manual approval/rejection only
            return current
        
        else:
            return current
    
    def _build_transition_conditions(
        self,
        application: KYCApplication,
        verification_results: Optional[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Build conditions map for transition validation"""
        
        conditions = {
            "has_required_documents": self._has_required_documents(application),
            "has_customer_data": self._has_customer_data(application),
            "documents_uploaded": len(application.documents) > 0,
            "documents_verified": self._documents_verified(application),
            "all_checks_passed": self._all_checks_passed(application, verification_results),
            "application_expired": self._is_expired(application)
        }
        
        # Score-based conditions
        if verification_results:
            overall = verification_results.get("overall_confidence_score", 0)
            conditions["high_confidence_score"] = overall >= settings.AUTO_APPROVE_THRESHOLD
            conditions["medium_confidence_score"] = overall >= settings.MANUAL_REVIEW_THRESHOLD
            conditions["low_confidence_score"] = overall < settings.MANUAL_REVIEW_THRESHOLD
            conditions["failed_verification"] = overall < 0.5
        else:
            conditions["high_confidence_score"] = False
            conditions["medium_confidence_score"] = False
            conditions["low_confidence_score"] = False
            conditions["failed_verification"] = False
        
        return conditions
    
    def _has_required_documents(self, application: KYCApplication) -> bool:
        """Check if all required documents are uploaded"""
        required_types = ["cin_front", "cin_back", "selfie"]
        uploaded_types = [doc.document_type for doc in application.documents]
        return all(dtype in uploaded_types for dtype in required_types)
    
    def _has_customer_data(self, application: KYCApplication) -> bool:
        """Check if customer data is complete"""
        return all([
            application.cin_number,
            application.first_name,
            application.last_name,
            application.date_of_birth
        ])
    
    def _documents_verified(self, application: KYCApplication) -> bool:
        """Check if documents are verified"""
        verified_docs = [
            doc for doc in application.documents 
            if doc.status == "verified"
        ]
        return len(verified_docs) >= 2  # At least CIN front/back
    
    def _all_checks_passed(
        self,
        application: KYCApplication,
        verification_results: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if all verifications passed"""
        if not verification_results:
            return False
        
        # Check all verification records
        verifications = application.verifications
        if not verifications:
            return False
        
        # All must pass
        return all(v.result == VerificationResult.PASS for v in verifications)
    
    def _is_expired(self, application: KYCApplication) -> bool:
        """Check if application is expired"""
        if not application.expires_at:
            return False
        return datetime.utcnow() > application.expires_at
    
    def _update_verification_scores(
        self,
        application: KYCApplication,
        results: Dict[str, Any]
    ):
        """Update application with verification scores"""
        if "document_verification_score" in results:
            application.document_verification_score = results["document_verification_score"]
        
        if "face_verification_score" in results:
            application.face_verification_score = results["face_verification_score"]
        
        if "overall_confidence_score" in results:
            application.overall_confidence_score = results["overall_confidence_score"]
        
        if "risk_score" in results:
            application.risk_score = results["risk_score"]
    
    async def _trigger_next_step(self, application: KYCApplication, new_state: str):
        """Trigger next workflow step (async tasks)"""
        
        # from app.integrations.queue import (
        #     trigger_document_verification,
        #     trigger_face_verification,
        #     send_approval_notification,
        #     send_rejection_notification,
        #     assign_to_agent
        # )
        # TODO: Implement Celery tasks later
        # For now, just log the workflow step
        logger.info(f"Workflow step triggered: {new_state} for application {application.id}")
        
         # Placeholder - actual processing will happen synchronously for now
        if new_state == KYCStatus.DOCUMENT_VERIFICATION:
            logger.info("TODO: Trigger document verification")
            # trigger_document_verification.delay(str(application.id))
        
        elif new_state == KYCStatus.FACE_VERIFICATION:
            logger.info("TODO: Trigger face verification")
            # trigger_face_verification.delay(str(application.id))
        
        elif new_state == KYCStatus.MANUAL_REVIEW:
            logger.info("TODO: Assign to agent")
            # assign_to_agent.delay(str(application.id))
        
        elif new_state == KYCStatus.APPROVED:
            logger.info("TODO: Send approval notification")
            # send_approval_notification.delay(str(application.id))
        
        elif new_state == KYCStatus.REJECTED:
            logger.info("TODO: Send rejection notification")
            # send_rejection_notification.delay(str(application.id))