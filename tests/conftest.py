"""Pytest configuration and fixtures for Falcon AI tests."""
import os
import sys
from pathlib import Path

# Set test environment BEFORE any app imports
# CRITICAL: Override .env settings for testing
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
# Use file-based SQLite database (not :memory:) to avoid thread issues
test_db_path = str(Path(__file__).resolve().parent / "test_falcon.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"
os.environ.setdefault("CORS_ORIGINS", "*")

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize test database with schema BEFORE any tests run."""
    # Import AFTER environment is set
    from app.database import engine, Base
    from app.models import User, Chat, Conversation, Memory, MemoryEmbedding
    
    # Drop existing tables if they exist
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables fresh
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n[SETUP] Created tables: {tables}")
    
    yield
    
    # Optional: cleanup after all tests
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Ensure test directories exist."""
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("data/chroma").mkdir(parents=True, exist_ok=True)


@pytest.fixture
def test_user():
    """Standard test user data."""
    return {
        "username": "pytestuser",
        "password": "testpassword",
        "email": "test@example.com"
    }


@pytest.fixture
def client():
    """Provide FastAPI TestClient with test database."""
    from starlette.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    from app.database import SessionLocal, Base, engine
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    session.close()
    
    # Clear any remaining state between tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


