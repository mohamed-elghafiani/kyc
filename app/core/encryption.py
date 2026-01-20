# app/core/encryption.py
from cryptography.fernet import Fernet
from typing import Optional
import base64

from app.config import settings


class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self):
        # In production, use key management service (KMS)
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return value
        
        encrypted = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted value"""
        if not encrypted_value:
            return encrypted_value
        
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        return decrypted_data


# Global encryption instance
encryption = FieldEncryption()


# Sensitive fields that should be encrypted
ENCRYPTED_FIELDS = [
    "cin_number",
    "first_name",
    "last_name",
    "date_of_birth",
    "place_of_birth",
    "phone_number",
    "email",
    "address"
]