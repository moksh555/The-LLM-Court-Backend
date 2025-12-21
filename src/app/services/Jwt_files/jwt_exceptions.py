class JwtError(Exception):
    """Base JWT Error"""

class ExpiredToken(JwtError):
    """Token Expired"""

class InvalidToken(JwtError):
    """Token Invalid"""
