# app/schemas/kyc.py
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from uuid import UUID
import re

from app.models.kyc_application import KYCStatus, RiskLevel
from app.config import settings


class AddressSchema(BaseModel):
    street: str
    city: str
    postal_code: Optional[str]
    province: str
    country: str = "Morocco"


class KYCApplicationCreate(BaseModel):
    # Personal Information
    cin_number: str = Field(..., min_length=7, max_length=10)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    place_of_birth: str
    nationality: str = "MA"
    
    # Contact
    phone_number: str = Field(..., pattern=r'^\+?212[0-9]{9}$')
    email: EmailStr
    address: AddressSchema
    
    # Optional
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('cin_number')
    def validate_cin(cls, v):
        if not re.match(settings.CIN_REGEX, v.upper()):
            raise ValueError('Invalid CIN format')
        return v.upper()
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Applicant must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "cin_number": "AB123456",
                "first_name": "Ahmed",
                "last_name": "Alami",
                "date_of_birth": "1990-01-15",
                "place_of_birth": "Casablanca",
                "nationality": "MA",
                "phone_number": "+212612345678",
                "email": "ahmed.alami@example.ma",
                "address": {
                    "street": "123 Rue Mohammed V",
                    "city": "Casablanca",
                    "postal_code": "20000",
                    "province": "Casablanca-Settat",
                    "country": "Morocco"
                }
            }
        }


class KYCApplicationUpdate(BaseModel):
    phone_number: Optional[str]
    email: Optional[EmailStr]
    address: Optional[AddressSchema]
    metadata: Optional[Dict[str, Any]]


class KYCApplicationResponse(BaseModel):
    id: UUID
    application_number: str
    status: KYCStatus
    risk_level: Optional[RiskLevel]
    overall_confidence_score: Optional[float]
    created_at: datetime
    submitted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class KYCApplicationDetail(KYCApplicationResponse):
    cin_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone_number: str
    email: str
    document_count: int
    verification_count: int
    assigned_agent_id: Optional[UUID]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]


class KYCApprovalRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000)


class KYCRejectionRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class KYCListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    applications: List[KYCApplicationResponse]