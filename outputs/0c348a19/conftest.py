# conftest.py
"""
Test configuration and fixtures for authentication system tests.
"""
import pytest
from typing import Dict, Any
from unittest.mock import Mock

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    db = Mock()
    db.get_user.return_value = None
    db.create_user.return_value = True
    db.update_user.return_value = True
    return db

@pytest.fixture
def valid_user_data() -> Dict[str, Any]:
    """Valid user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }

@pytest.fixture
def auth_service(mock_database):
    """Authentication service instance with mocked dependencies."""
    from auth_service import AuthenticationService
    return AuthenticationService(database=mock_database)