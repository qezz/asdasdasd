"""Exceptions raised by PyStorage"""

class AuthError(Exception):
    """Raised when server can't auth you"""

class UserExists(Exception):
    """Raised when attempted to create a user that is already exists"""

class RoleExists(Exception):
    """Raised when attempted to create a role that is already exists"""

class InvalidResponse(Exception):
    """Raised when expected response is not that provided"""

class NoFile(Exception):
    """When file not found"""

class InvalidFile(Exception):
    """When file's id doesn't not exist"""

class AlreadyExists(Exception):
    """File or directory already exists"""

class ConfigError(Exception):
    """Configuration error"""
