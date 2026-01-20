from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    kyc,
    documents,
    verification,
    audit,
    admin
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    kyc.router,
    prefix="/kyc",
    tags=["KYC Applications"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"]
)

api_router.include_router(
    verification.router,
    prefix="/verification",
    tags=["Verification"]
)

api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["Audit Logs"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Administration"]
)