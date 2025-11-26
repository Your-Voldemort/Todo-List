"""
Enhanced validation layer for Todo Application

This module provides comprehensive input validation for todos, categories, and search queries.
It ensures data integrity and security by validating all user inputs before they reach the database.
"""
import re
from typing import Tuple, Optional
from datetime import datetime, timezone


class TodoValidator:
    """Validator for Todo-related inputs"""
    
    @staticmethod
    def validate_title(title: str) -> Tuple[bool, Optional[str]]:
        """
        Validate todo title
        
        Args:
            title: The title string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if validation passes, False otherwise
            - error_message: None if valid, error description if invalid
        """
        if not title:
            return False, "Title is required"
        
        # Check if title is only whitespace
        if title.strip() == '':
            return False, "Title cannot contain only whitespace characters"
        
        # Check length constraints
        if len(title) > 100:
            return False, "Title must be 100 characters or less"
        
        return True, None
    
    @staticmethod
    def validate_due_date(due_date: Optional[datetime]) -> Tuple[bool, Optional[str]]:
        """
        Validate due date
        
        Args:
            due_date: The datetime to validate (can be None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Due date is optional
        if due_date is None:
            return True, None
        
        # Ensure it's a datetime object
        if not isinstance(due_date, datetime):
            return False, "Due date must be a valid datetime"
        
        # Past dates are allowed (they'll be marked as overdue)
        # This validates requirement 2.4
        return True, None
    
    @staticmethod
    def validate_description(description: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate todo description
        
        Args:
            description: The description string to validate (can be None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Description is optional
        if description is None or description == '':
            return True, None
        
        # Check length constraints
        if len(description) > 1000:
            return False, "Description must be 1000 characters or less"
        
        return True, None


class CategoryValidator:
    """Validator for Category-related inputs"""
    
    # Regex pattern for hex color validation (#RRGGBB format)
    HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    @staticmethod
    def validate_color(color: str) -> Tuple[bool, Optional[str]]:
        """
        Validate hex color format
        
        Args:
            color: The color string to validate (should be #RRGGBB format)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not color:
            return False, "Color is required"
        
        # Check if it matches the hex color pattern
        if not CategoryValidator.HEX_COLOR_PATTERN.match(color):
            return False, "Color must be in hex format (#RRGGBB, e.g., #FF5733)"
        
        return True, None
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate category name
        
        Args:
            name: The category name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Category name is required"
        
        # Check if name is only whitespace
        if name.strip() == '':
            return False, "Category name cannot contain only whitespace characters"
        
        # Check length constraints
        if len(name) > 50:
            return False, "Category name must be 50 characters or less"
        
        return True, None


class SearchValidator:
    """Validator for search query inputs"""
    
    # Maximum search query length
    MAX_QUERY_LENGTH = 500
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize search query for safe SQL execution
        
        This method ensures that special SQL characters are handled safely.
        SQLAlchemy's ilike() already provides parameterization, but we add
        an extra layer of safety by limiting length and normalizing Unicode.
        
        Args:
            query: The raw search query string
            
        Returns:
            Sanitized query string safe for database operations
        """
        if not query:
            return ''
        
        # Strip leading/trailing whitespace
        sanitized = query.strip()
        
        # Truncate to maximum length
        if len(sanitized) > SearchValidator.MAX_QUERY_LENGTH:
            sanitized = sanitized[:SearchValidator.MAX_QUERY_LENGTH]
        
        # Unicode normalization (NFC form - canonical composition)
        # This ensures consistent representation of Unicode characters
        import unicodedata
        sanitized = unicodedata.normalize('NFC', sanitized)
        
        # SQLAlchemy's ilike() will handle escaping of special characters
        # We don't need to manually escape % or _ as they're handled by the ORM
        
        return sanitized
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate search query
        
        Args:
            query: The search query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Empty queries are allowed (returns all results)
        if not query or query.strip() == '':
            return True, None
        
        # Check length
        if len(query) > SearchValidator.MAX_QUERY_LENGTH:
            return False, f"Search query must be {SearchValidator.MAX_QUERY_LENGTH} characters or less"
        
        return True, None


class AuthenticationValidator:
    """Validator for authentication-related inputs"""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate username
        
        Args:
            username: The username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if username.strip() == '':
            return False, "Username cannot contain only whitespace characters"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 80:
            return False, "Username must be 80 characters or less"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format
        
        Args:
            email: The email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic email pattern validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return False, "Invalid email format"
        
        if len(email) > 120:
            return False, "Email must be 120 characters or less"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        return True, None


# Helper functions for common validation patterns
def is_valid_hex_color(color: str) -> bool:
    """
    Quick check if a string is a valid hex color
    
    Args:
        color: String to check
        
    Returns:
        True if valid hex color, False otherwise
    """
    return CategoryValidator.validate_color(color)[0]


def is_whitespace_only(text: str) -> bool:
    """
    Check if a string contains only whitespace characters
    
    Args:
        text: String to check
        
    Returns:
        True if string is only whitespace, False otherwise
    """
    return text is not None and text.strip() == ''


def sanitize_search_input(query: str) -> str:
    """
    Convenience function to sanitize search input
    
    Args:
        query: Raw search query
        
    Returns:
        Sanitized query string
    """
    return SearchValidator.sanitize_query(query)
