#!/bin/bash

# ============================================
# KYC Backend - Database Backup Script
# ============================================

set -e

# Configuration
BACKUP_DIR="/var/backups/kyc-backend"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment variables
source .env

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "============================================"
echo "KYC Backend - Database Backup"
echo "============================================"
echo "Timestamp: $TIMESTAMP"
echo ""

# PostgreSQL Backup
echo "Backing up PostgreSQL database..."
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h localhost \
    -U $DB_USER \
    -d $DB_NAME \
    -F c \
    -f "$BACKUP_DIR/kyc_db_$TIMESTAMP.dump"

echo "PostgreSQL backup completed"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_DIR/kyc_db_$TIMESTAMP.dump"
echo "Compression completed"

# Backup MinIO data (optional)
echo "Backing up MinIO data..."
mc mirror myminio/kyc-documents "$BACKUP_DIR/minio_documents_$TIMESTAMP"
mc mirror myminio/kyc-photos "$BACKUP_DIR/minio_photos_$TIMESTAMP"
tar -czf "$BACKUP_DIR/minio_data_$TIMESTAMP.tar.gz" \
    "$BACKUP_DIR/minio_documents_$TIMESTAMP" \
    "$BACKUP_DIR/minio_photos_$TIMESTAMP"
rm -rf "$BACKUP_DIR/minio_documents_$TIMESTAMP" "$BACKUP_DIR/minio_photos_$TIMESTAMP"
echo "MinIO backup completed"

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo "Cleanup completed"

# Backup summary
echo ""
echo "============================================"
echo "Backup Summary"
echo "============================================"
echo "Backup location: $BACKUP_DIR"
echo "Files created:"
ls -lh "$BACKUP_DIR"/*_$TIMESTAMP.*
echo ""
echo "Backup completed successfully!"
echo "============================================"