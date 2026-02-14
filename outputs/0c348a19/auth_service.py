# auth_service.py
"""
Authentication service for user management.
"""
import re
import hashlib
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class User:
    """User data model."""
    username: str
    email: str
    password_hash: str
    is_active: bool = True

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class AuthenticationService:
    """Service for handling user authentication operations."""
    
    def __init__(self, database):
        self.database = database
        self.min_password_length = 8
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        return bool(self.email_pattern.match(email))
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password or not isinstance(password, str):
            return False, "Password is required"
        
        if len(password) < self.min_password_length:
            return False, f"Password must be at least {self.min_password_length} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: User's chosen username
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with success status and message
            
        Raises:
            AuthenticationError: If registration fails
        """
        # Validate inputs
        if not username or not isinstance(username, str) or len(username.strip()) < 3:
            raise AuthenticationError("Username must be at least 3 characters long")
        
        if not self.validate_email(email):
            raise AuthenticationError("Invalid email format")
        
        is_valid_password, password_error = self.validate_password(password)
        if not is_valid_password:
            raise AuthenticationError(password_error)
        
        # Check if user already exists
        existing_user = self.database.get_user(username=username)
        if existing_user:
            raise AuthenticationError("Username already exists")
        
        existing_email = self.database.get_user(email=email)
        if existing_email:
            raise AuthenticationError("Email already registered")
        
        # Create user
        password_hash = self.hash_password(password)
        user = User(
            username=username.strip(),
            email=email.lower().strip(),
            password_hash=password_hash
        )
        
        success = self.database.create_user(user)
        if not success:
            raise AuthenticationError("Failed to create user")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "username": user.username
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username or email
            password: User's password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if not username or not password:
            return None
        
        # Try to find user by username or email
        user = self.database.get_user(username=username)
        if not user:
            user = self.database.get_user(email=username)
        
        if not user or not user.is_active:
            return None
        
        # Verify password
        password_hash = self.hash_password(password)
        if password_hash != user.password_hash:
            return None
        
        return user