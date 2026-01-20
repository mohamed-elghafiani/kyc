#!/bin/bash

# ============================================
# KYC Backend - Database Restore Script
# ============================================

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /var/backups/kyc-backend/kyc_db_20240101_120000.dump.gz"
    exit 1
fi

BACKUP_FILE=$1

# Load environment variables
source .env

echo "============================================"
echo "KYC Backend - Database Restore"
echo "============================================"
echo "Backup file: $BACKUP_FILE"
echo ""

# Confirm restore
read -p "This will OVERWRITE the current database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > /tmp/kyc_restore.dump
    RESTORE_FILE=/tmp/kyc_restore.dump
else
    RESTORE_FILE=$BACKUP_FILE
fi

# Drop and recreate database
echo "Dropping existing database..."
PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# Restore database
echo "Restoring database..."
PGPASSWORD=$DB_PASSWORD pg_restore \
    -h localhost \
    -U $DB_USER \
    -d $DB_NAME \
    -v \
    "$RESTORE_FILE"

# Cleanup
if [ "$RESTORE_FILE" = "/tmp/kyc_restore.dump" ]; then
    rm /tmp/kyc_restore.dump
fi

echo ""
echo "============================================"
echo "Database restored successfully!"
echo "============================================"