# app/core/exceptions.py
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class KYCException(HTTPException):
    """Base exception for KYC system"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


class ApplicationNotFoundException(KYCException):
    def __init__(self, application_id: str):
        super().__init__(
            error_code="APPLICATION_NOT_FOUND",
            message=f"Application {application_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidStatusTransitionException(KYCException):
    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            error_code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition from {from_status} to {to_status}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DuplicateApplicationException(KYCException):
    def __init__(self, cin_number: str):
        super().__init__(
            error_code="DUPLICATE_APPLICATION",
            message=f"Active application already exists for CIN {cin_number}",
            status_code=status.HTTP_409_CONFLICT
        )


class DocumentProcessingException(KYCException):
    def __init__(self, message: str):
        super().__init__(
            error_code="DOCUMENT_PROCESSING_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class InsufficientPermissionsException(KYCException):
    def __init__(self, required_role: str):
        super().__init__(
            error_code="INSUFFICIENT_PERMISSIONS",
            message=f"Required role: {required_role}",
            status_code=status.HTTP_403_FORBIDDEN
        )


class VerificationFailedException(KYCException):
    def __init__(self, verification_type: str, reason: str):
        super().__init__(
            error_code="VERIFICATION_FAILED",
            message=f"{verification_type} verification failed: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )