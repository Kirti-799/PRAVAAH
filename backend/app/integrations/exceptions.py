"""
backend/app/integrations/exceptions.py

Domain-specific exceptions for external provider integrations in PRAVAAH.
Standardizes error classification across weather, hydrological, and mapping adapters.
"""

from typing import Optional


class ProviderIntegrationError(Exception):
    """Base exception for all external provider integration failures."""
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


class ProviderTimeoutError(ProviderIntegrationError):
    """Raised when an external provider request exceeds the configured timeout."""
    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(provider, f"Request timed out after {timeout_seconds:.1f}s", status_code=504)


class ProviderRateLimitError(ProviderIntegrationError):
    """Raised when an external provider responds with HTTP 429 Too Many Requests."""
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(provider, msg, status_code=429)


class ProviderUnavailableError(ProviderIntegrationError):
    """Raised when an external provider responds with 5xx or connection fails."""
    def __init__(self, provider: str, message: str = "Provider service unavailable"):
        super().__init__(provider, message, status_code=503)


class ProviderResponseValidationError(ProviderIntegrationError):
    """Raised when an external provider returns malformed, unexpected, or unparseable data."""
    def __init__(self, provider: str, details: str):
        super().__init__(provider, f"Malformed response payload: {details}", status_code=502)
