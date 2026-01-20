#!/usr/bin/env python3
"""
Generate security keys for the application
"""

import secrets
from cryptography.fernet import Fernet

print("="*60)
print("KYC Backend - Security Keys Generator")
print("="*60)
print("\nGenerated keys (add to .env file):\n")

# Generate SECRET_KEY for JWT
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")

# Generate ENCRYPTION_KEY for Fernet
encryption_key = Fernet.generate_key().decode()
print(f"ENCRYPTION_KEY={encryption_key}")

# Generate random passwords
db_password = secrets.token_urlsafe(24)
redis_password = secrets.token_urlsafe(24)
minio_password = secrets.token_urlsafe(24)

print(f"\nDB_PASSWORD={db_password}")
print(f"REDIS_PASSWORD={redis_password}")
print(f"MINIO_ROOT_PASSWORD={minio_password}")

print("\n" + "="*60)
print("Store these keys securely!")
print("="*60)