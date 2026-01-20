#!/usr/bin/env python3
"""
Create admin user for the system
"""

import sys
import os
import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """Create admin user interactively"""
    db: Session = SessionLocal()
    
    try:
        print("\n" + "="*50)
        print("KYC Backend - Create Admin User")
        print("="*50 + "\n")
        
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        full_name = input("Enter full name: ").strip()
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            logger.error("User with this username or email already exists")
            sys.exit(1)
        
        # Get password
        while True:
            password = getpass.getpass("Enter password: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                print("Passwords don't match. Try again.")
                continue
            
            if len(password) < 12:
                print("Password must be at least 12 characters")
                continue
            
            break
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "="*50)
        print("Admin user created successfully!")
        print("="*50)
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print("="*50 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()