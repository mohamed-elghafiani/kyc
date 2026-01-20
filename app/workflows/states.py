# app/workflows/states.py
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.models.kyc_application import KYCStatus


class WorkflowState(str, Enum):
    """KYC Workflow States"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENT_VERIFICATION = "document_verification"
    FACE_VERIFICATION = "face_verification"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class StateTransition:
    """Defines allowed state transitions"""
    from_state: WorkflowState
    to_state: WorkflowState
    required_conditions: List[str]
    allowed_roles: List[str]


# Define workflow transitions
WORKFLOW_TRANSITIONS: List[StateTransition] = [
    # Draft to Submitted
    StateTransition(
        from_state=WorkflowState.DRAFT,
        to_state=WorkflowState.SUBMITTED,
        required_conditions=["has_required_documents", "has_customer_data"],
        allowed_roles=["api_client", "agent"]
    ),
    
    # Submitted to Document Verification
    StateTransition(
        from_state=WorkflowState.SUBMITTED,
        to_state=WorkflowState.DOCUMENT_VERIFICATION,
        required_conditions=["documents_uploaded"],
        allowed_roles=["system"]
    ),
    
    # Document Verification to Face Verification
    StateTransition(
        from_state=WorkflowState.DOCUMENT_VERIFICATION,
        to_state=WorkflowState.FACE_VERIFICATION,
        required_conditions=["documents_verified"],
        allowed_roles=["system"]
    ),
    
    # Document Verification to Manual Review (if score low)
    StateTransition(
        from_state=WorkflowState.DOCUMENT_VERIFICATION,
        to_state=WorkflowState.MANUAL_REVIEW,
        required_conditions=["low_confidence_score"],
        allowed_roles=["system"]
    ),
    
    # Face Verification to Approved (auto-approve)
    StateTransition(
        from_state=WorkflowState.FACE_VERIFICATION,
        to_state=WorkflowState.APPROVED,
        required_conditions=["high_confidence_score", "all_checks_passed"],
        allowed_roles=["system"]
    ),
    
    # Face Verification to Manual Review
    StateTransition(
        from_state=WorkflowState.FACE_VERIFICATION,
        to_state=WorkflowState.MANUAL_REVIEW,
        required_conditions=["medium_confidence_score"],
        allowed_roles=["system"]
    ),
    
    # Face Verification to Rejected (auto-reject)
    StateTransition(
        from_state=WorkflowState.FACE_VERIFICATION,
        to_state=WorkflowState.REJECTED,
        required_conditions=["failed_verification"],
        allowed_roles=["system"]
    ),
    
    # Manual Review to Approved
    StateTransition(
        from_state=WorkflowState.MANUAL_REVIEW,
        to_state=WorkflowState.APPROVED,
        required_conditions=["agent_approved"],
        allowed_roles=["agent", "supervisor"]
    ),
    
    # Manual Review to Rejected
    StateTransition(
        from_state=WorkflowState.MANUAL_REVIEW,
        to_state=WorkflowState.REJECTED,
        required_conditions=["agent_rejected"],
        allowed_roles=["agent", "supervisor"]
    ),
    
    # Any state to Expired (system only)
    StateTransition(
        from_state=WorkflowState.SUBMITTED,
        to_state=WorkflowState.EXPIRED,
        required_conditions=["application_expired"],
        allowed_roles=["system"]
    ),
]


class WorkflowEngine:
    """State machine for KYC workflow"""
    
    def __init__(self):
        self.transitions = {
            (t.from_state, t.to_state): t for t in WORKFLOW_TRANSITIONS
        }
    
    def can_transition(
        self,
        from_state: str,
        to_state: str,
        conditions: Dict[str, bool],
        user_role: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if transition is allowed
        Returns: (is_allowed, reason_if_not)
        """
        transition = self.transitions.get((from_state, to_state))
        
        if not transition:
            return False, f"No transition defined from {from_state} to {to_state}"
        
        # Check role
        if user_role not in transition.allowed_roles:
            return False, f"Role {user_role} not allowed for this transition"
        
        # Check conditions
        for condition in transition.required_conditions:
            if not conditions.get(condition, False):
                return False, f"Required condition not met: {condition}"
        
        return True, None
    
    def get_next_states(self, current_state: str) -> List[str]:
        """Get all possible next states from current state"""
        return [
            to_state 
            for (from_state, to_state) in self.transitions.keys() 
            if from_state == current_state
        ]


workflow_engine = WorkflowEngine()