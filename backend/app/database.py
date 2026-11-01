import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load environment variables from the project's .env file
load_dotenv()


# Read the PostgreSQL connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Please configure it in the project's .env file."
    )


# Create the database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Database dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
