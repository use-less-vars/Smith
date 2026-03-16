"""
Provider-specific exceptions for error handling.
"""

class ProviderError(Exception):
    """Base exception for provider errors"""
    pass

class ProviderNotFoundError(ProviderError):
    """Raised when requested provider type is not registered"""
    pass

class InvalidConfigError(ProviderError):
    """Raised when provider configuration is invalid"""
    pass

class AuthenticationError(ProviderError):
    """Raised when API authentication fails"""
    pass

class RateLimitExceeded(ProviderError):
    """Raised when rate limit is exceeded"""
    pass

class RateLimitError(RateLimitExceeded):
    """Alias for backward compatibility"""
    pass

class ModelNotFoundError(ProviderError):
    """Raised when specified model is not available"""
    pass

class TokenLimitExceededError(ProviderError):
    """Raised when token limit is exceeded"""
    pass

class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out"""
    pass

class ToolFormatError(ProviderError):
    """Raised when tool format conversion fails"""
    pass