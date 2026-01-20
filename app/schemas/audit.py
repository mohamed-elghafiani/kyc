# app/schemas/audit.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    description: str
    username: Optional[str]
    ip_address: str
    timestamp: datetime
    changes: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True