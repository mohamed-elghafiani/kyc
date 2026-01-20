from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, EmailStr

from app.dependencies import get_db, require_admin
from app.models.user import User, UserRole, UserStatus
from app.core.security import hash_password
from app.schemas.user import UserResponse, UserCreate

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create new user (admin only)
    """
    
    # Check if username exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role if hasattr(user_data, 'role') else UserRole.AGENT,
        created_by=current_user.id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users (admin only)
    """
    
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    status: UserStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user status (activate/deactivate/suspend)
    """
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = status
    user.is_active = (status == UserStatus.ACTIVE)
    
    db.commit()
    
    return {"message": f"User status updated to {status}"}


@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get system statistics (admin dashboard)
    """
    
    from app.models.kyc_application import KYCApplication, KYCStatus
    from sqlalchemy import func
    
    # Total applications
    total_applications = db.query(func.count(KYCApplication.id)).scalar()
    
    # By status
    status_counts = db.query(
        KYCApplication.status,
        func.count(KYCApplication.id)
    ).group_by(KYCApplication.status).all()
    
    # Pending review
    pending_review = db.query(func.count(KYCApplication.id)).filter(
        KYCApplication.status == KYCStatus.MANUAL_REVIEW
    ).scalar()
    
    # Today's submissions
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_submissions = db.query(func.count(KYCApplication.id)).filter(
        KYCApplication.created_at >= today_start
    ).scalar()
    
    return {
        "total_applications": total_applications,
        "status_breakdown": {status: count for status, count in status_counts},
        "pending_review": pending_review,
        "today_submissions": today_submissions
    }