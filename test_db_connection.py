# test_db_connection.py
from sqlalchemy import create_engine, text
from app.config import settings

print("Testing Neon PostgreSQL connection...")
print(f"Database URL: {settings.DATABASE_URL.split('@')[1]}")  # Hide password

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print("\n✅ SUCCESS! Connected to PostgreSQL")
        print(f"Version: {version}")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")