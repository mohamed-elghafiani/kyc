# # app/integrations/storage.py
# """
# MinIO Storage - OPTIONAL
# Only loads if minio package is installed
# """

# try:
#     from minio import Minio
#     from minio.error import S3Error
#     from datetime import timedelta
#     import io
#     import logging
    
#     logger = logging.getLogger(__name__)
    
#     class StorageService:
#         """MinIO/S3 compatible storage service"""
        
#         def __init__(self):
#             from app.config import settings
#             self.client = Minio(
#                 settings.STORAGE_ENDPOINT,
#                 access_key=settings.STORAGE_ACCESS_KEY,
#                 secret_key=settings.STORAGE_SECRET_KEY,
#                 secure=settings.STORAGE_SECURE
#             )
#             self.buckets = {
#                 "documents": settings.STORAGE_BUCKET_DOCUMENTS,
#                 "photos": settings.STORAGE_BUCKET_PHOTOS
#             }
        
#         # ... rest of the code stays the same ...
    
#     storage_service = StorageService()

# except ImportError:
#     logger = logging.getLogger(__name__)
#     logger.warning("⚠️  MinIO not installed. Use storage_local.py instead")
    
#     # Dummy class
#     class StorageService:
#         def __init__(self):
#             raise ImportError("MinIO not installed. Set STORAGE_TYPE='local' in .env")
    
#     storage_service = None