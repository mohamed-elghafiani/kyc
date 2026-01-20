# app/integrations/storage_local.py
import os
import shutil
from pathlib import Path
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Local filesystem storage (alternative to MinIO)"""
    
    def __init__(self):
        self.base_path = Path(settings.STORAGE_LOCAL_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def ensure_buckets_exist(self):
        """Create local directories for buckets"""
        buckets = ["documents", "photos"]
        for bucket in buckets:
            bucket_path = self.base_path / bucket
            bucket_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created local bucket: {bucket_path}")
    
    async def upload_file(
        self,
        bucket: str,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """Upload file to local filesystem"""
        
        # Create full path
        file_path = self.base_path / bucket / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Uploaded file to {file_path}")
        return str(file_path.relative_to(self.base_path))
    
    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """Download file from local filesystem"""
        
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file from local filesystem"""
        
        full_path = self.base_path / file_path
        
        if full_path.exists():
            full_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        
        return False
    
    async def get_file_url(
        self,
        bucket: str,
        file_path: str,
        expires_seconds: int = 3600
    ) -> str:
        """Return local file path (no presigned URL needed)"""
        return str(self.base_path / file_path)


# Factory function to get appropriate storage service
def get_storage_service():
    """Get storage service based on configuration"""
    if settings.STORAGE_TYPE == "local":
        return LocalStorageService()
    else:
        from app.integrations.storage import StorageService
        return StorageService()


# Global storage service
storage_service = get_storage_service()