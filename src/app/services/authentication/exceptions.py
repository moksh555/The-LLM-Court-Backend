# app/schemas/authentication/exceptions.py

class AuthError(Exception):
    """Base auth error."""


class InvalidCredentials(AuthError):
    """Email not found OR password mismatch."""


class OAuthOnlyAccount(AuthError):
    """User exists but has no password hash (e.g., Google-only)."""


class AuthDependencyError(AuthError):
    """Downstream dependency failed (DynamoDB, config, etc.)."""

class RegisterFirstNameError(AuthError):
    """First Name Empty Error: Register Service"""

class RegisterEmailError(AuthError):
    """Email Empty Error: Register Service"""

class RegisterPasswordError(AuthError):
    """Password Empty Error: Register Service"""

class UserExistsError(AuthError):
    """User with same email already exists: Register Service"""

class RegisterDOBError(AuthError):
    """Date-OF-Birth Empty Error: Register Service"""

class UserUnAuthorizedNoToken(AuthError):
    """No Token Attached User Un-Authorized"""

class UserUnAuthorizedNoId(AuthError):
    """No user with user_id"""

class UserUnAuthorizedInvalidToken(AuthError):
    """User id and user mail does not match"""