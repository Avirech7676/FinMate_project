from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for development to make it easy, can switch to postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finmate.db")

# To use Postgres, just set the DATABASE_URL environment variable:
# DATABASE_URL = "postgresql://user:password@localhost/dbname"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL on Render - use connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True  # Verify connections before using
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
