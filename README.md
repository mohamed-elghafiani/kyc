# 🏦 KYC Backend System for Moroccan Banks

Production-ready, on-premise KYC (Know Your Customer) verification system built with FastAPI, designed specifically for Moroccan banking institutions.

## 🎯 Features

### Core Capabilities

- ✅ **Moroccan CIN Processing**: OCR extraction from Moroccan National ID cards
- ✅ **Face Verification**: Biometric face matching between document and selfie
- ✅ **Liveness Detection**: Anti-spoofing protection
- ✅ **Workflow Management**: State-machine-based KYC workflow
- ✅ **Risk Assessment**: AI-powered fraud detection and risk scoring
- ✅ **Audit Trail**: Complete compliance logging (7-year retention)
- ✅ **Multi-role Support**: Admin, Agent, Supervisor, Auditor roles

### Security & Compliance

- 🔐 Field-level encryption for PII
- 🔐 JWT-based authentication with refresh tokens
- 🔐 Role-based access control (RBAC)
- 🔐 Rate limiting and DDoS protection
- 🔐 GDPR compliance features
- 🔐 Complete audit logging

### Technical Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)
- **Queue**: Celery
- **AI/ML**: EasyOCR, Face Recognition, PyTorch
- **Deployment**: Docker, Docker Compose, Nginx

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/mohamed-elghafiani/kyc.git
cd kyc
```
