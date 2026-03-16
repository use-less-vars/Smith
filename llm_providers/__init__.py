"""
LLM Providers module for multi-provider support.
Implements Adapter pattern for normalizing different LLM provider APIs.
"""

from .base import (
    LLMProvider,
    LLMResponse,
    ProviderConfig,
)

from .factory import ProviderFactory
from .exceptions import (
    ProviderNotFoundError,
    InvalidConfigError,
    ProviderError,
)

from .openai_compatible import OpenAICompatibleProvider
# Note: AnthropicProvider will be imported when implemented in Phase 2

__all__ = [
    "LLMProvider",
    "LLMResponse", 
    "ProviderConfig",
    "ProviderFactory",
    "ProviderNotFoundError",
    "InvalidConfigError",
    "ProviderError",
    "OpenAICompatibleProvider",
]