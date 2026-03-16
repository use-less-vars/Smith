"""
Orchestrator for managing LLM provider chains, fallbacks, and retries.
Implements intelligent provider selection with cost-aware routing.
"""
import time
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from .base import LLMProvider, LLMResponse
from .factory import ProviderFactory
from .exceptions import ProviderError, RateLimitExceeded, AuthenticationError
from config import LLMConfig, FallbackConfig, BudgetConfig

logger = logging.getLogger(__name__)

class ProviderSelectionStrategy(str, Enum):
    """Strategy for selecting providers in a chain"""
    SEQUENTIAL = "sequential"  # Try providers in order, fallback on failure
    COST_AWARE = "cost_aware"  # Select cheapest provider that meets requirements
    PERFORMANCE = "performance"  # Select fastest provider (latency-based)
    ROUND_ROBIN = "round_robin"  # Rotate through providers

class LLMOrchestrator:
    """
    Orchestrates multiple LLM providers with fallback, retry, and budget management.
    
    Features:
    - Provider chains with configurable fallback strategies
    - Automatic retries with exponential backoff
    - Budget tracking and enforcement
    - Cost-aware provider selection
    - Usage statistics aggregation
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: LLMConfig containing provider, fallback, and budget settings
        """
        self.config = config
        self.provider_chain = self._create_provider_chain()
        self.current_provider_index = 0
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_latency_ms": 0.0,
            "provider_usage": {}  # Provider-specific usage stats
        }
        
        # Initialize provider usage tracking
        for provider in self.provider_chain:
            self.usage_stats["provider_usage"][provider.provider_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "cost": 0.0,
                "tokens": 0,
                "latency_ms": 0.0
            }
        
        logger.info(f"Initialized LLMOrchestrator with {len(self.provider_chain)} providers")
        logger.info(f"Primary provider: {self.provider_chain[0].provider_name}")
        if len(self.provider_chain) > 1:
            logger.info(f"Fallback providers: {[p.provider_name for p in self.provider_chain[1:]]}")
    
    def _create_provider_chain(self) -> List[LLMProvider]:
        """Create provider instances from configuration"""
        providers = []
        
        # Add primary provider
        primary_config = self.config.primary_provider
        primary_provider = ProviderFactory.create_from_dict(
            primary_config.dict(exclude_none=True)
        )
        providers.append(primary_provider)
        
        # Add fallback providers if configured
        if self.config.fallback_chain:
            for fallback_config in self.config.fallback_chain.providers:
                fallback_provider = ProviderFactory.create_from_dict(
                    fallback_config.dict(exclude_none=True)
                )
                providers.append(fallback_provider)
        
        return providers
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Execute chat completion with automatic fallback and retries.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            max_retries: Maximum retry attempts (overrides config)
            **kwargs: Additional completion parameters
            
        Returns:
            LLMResponse from successful completion
            
        Raises:
            ProviderError: If all providers fail after retries
        """
        start_time = time.time()
        self.usage_stats["total_requests"] += 1
        
        # Determine retry settings
        if max_retries is None:
            max_retries = self.config.fallback_chain.max_total_attempts if self.config.fallback_chain else 3
        
        # Try providers with retries
        last_error = None
        total_attempts = 0
        
        for attempt in range(max_retries):
            total_attempts += 1
            
            # Select provider for this attempt
            provider = self._select_provider(attempt, last_error)
            
            try:
                # Check budget before proceeding
                if not self._check_budget():
                    raise ProviderError("Budget limit exceeded")
                
                # Execute completion
                response = provider.chat_completion(messages, tools, **kwargs)
                
                # Update usage statistics
                self._track_provider_usage(provider, response, start_time)
                self.usage_stats["successful_requests"] += 1
                
                logger.debug(f"Request completed with provider: {provider.provider_name}")
                return response
                
            except (RateLimitExceeded, AuthenticationError) as e:
                # Provider-specific errors that should trigger fallback
                last_error = e
                logger.warning(f"Provider {provider.provider_name} failed: {e}. Trying next provider...")
                self._track_provider_failure(provider, e)
                
                # Mark provider as temporarily unavailable
                self._mark_provider_unavailable(provider)
                
                # Delay before next attempt
                if attempt < max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    time.sleep(delay)
                    
            except Exception as e:
                # Other errors
                last_error = e
                logger.warning(f"Provider {provider.provider_name} error: {e}")
                self._track_provider_failure(provider, e)
                
                # Delay before retry
                if attempt < max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    time.sleep(delay)
        
        # All attempts failed
        self.usage_stats["failed_requests"] += 1
        error_msg = f"All providers failed after {total_attempts} attempts"
        if last_error:
            error_msg += f". Last error: {last_error}"
        raise ProviderError(error_msg)
    
    def _select_provider(self, attempt: int, last_error: Any = None) -> LLMProvider:
        """
        Select provider for current attempt based on strategy and state.
        
        Args:
            attempt: Current attempt number (0-based)
            last_error: Error from previous attempt (if any)
            
        Returns:
            Selected LLMProvider instance
        """
        # Default to sequential strategy
        strategy = ProviderSelectionStrategy.SEQUENTIAL
        
        # Check if we should use a different strategy based on config
        # For now, implement sequential with fallback
        if attempt < len(self.provider_chain):
            return self.provider_chain[attempt]
        else:
            # Wrap around to primary provider
            return self.provider_chain[0]
    
    def _track_provider_usage(self, provider: LLMProvider, response: LLMResponse, start_time: float):
        """Track usage statistics for a provider"""
        provider_name = provider.provider_name
        provider_stats = self.usage_stats["provider_usage"][provider_name]
        
        # Update provider stats
        provider_stats["requests"] += 1
        provider_stats["successes"] += 1
        
        if response.usage:
            provider_stats["tokens"] += response.usage.get("total_tokens", 0)
        
        provider_stats["latency_ms"] += response.latency_ms
        
        # Get cost from provider's usage stats
        provider_usage = provider.get_usage_stats()
        provider_stats["cost"] = provider_usage["total_cost"]
        
        # Update global stats
        self.usage_stats["total_cost"] = sum(
            p["cost"] for p in self.usage_stats["provider_usage"].values()
        )
        self.usage_stats["total_tokens"] = sum(
            p["tokens"] for p in self.usage_stats["provider_usage"].values()
        )
        self.usage_stats["total_latency_ms"] = sum(
            p["latency_ms"] for p in self.usage_stats["provider_usage"].values()
        )
    
    def _track_provider_failure(self, provider: LLMProvider, error: Exception):
        """Track failure statistics for a provider"""
        provider_name = provider.provider_name
        provider_stats = self.usage_stats["provider_usage"][provider_name]
        provider_stats["requests"] += 1
        provider_stats["failures"] += 1
    
    def _mark_provider_unavailable(self, provider: LLMProvider):
        """
        Mark provider as temporarily unavailable.
        In a more sophisticated implementation, this could track
        provider health and exclude unhealthy providers.
        """
        # Simple implementation: do nothing, rely on sequential fallback
        # Could be extended to implement circuit breaker pattern
        pass
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retries"""
        base_delay = 1.0
        if self.config.fallback_chain:
            base_delay = self.config.fallback_chain.retry_delay
        
        # Exponential backoff with jitter
        delay = base_delay * (2 ** attempt)
        jitter = delay * 0.1  # ±10% jitter
        delay += jitter * (hash(str(time.time())) % 2000 - 1000) / 1000
        
        return max(0.1, min(delay, 30.0))  # Cap between 0.1 and 30 seconds
    
    def _check_budget(self) -> bool:
        """Check if current usage is within budget limits"""
        if not self.config.budget:
            return True
        
        validation = self.config.validate_budget(
            current_cost=self.usage_stats["total_cost"],
            current_tokens=self.usage_stats["total_tokens"],
            current_requests=self.usage_stats["total_requests"]
        )
        
        if validation["stop_required"]:
            logger.error(f"Budget exceeded: {validation['warnings']}")
            return False
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(f"Budget warning: {warning}")
        
        return True
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        stats = self.usage_stats.copy()
        
        # Calculate success rate
        total = stats["total_requests"]
        if total > 0:
            stats["success_rate"] = (stats["successful_requests"] / total) * 100
            stats["failure_rate"] = (stats["failed_requests"] / total) * 100
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
        
        # Add average latency
        if stats["successful_requests"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["successful_requests"]
        else:
            stats["avg_latency_ms"] = 0.0
        
        # Add cost per token
        if stats["total_tokens"] > 0:
            stats["cost_per_token"] = stats["total_cost"] / stats["total_tokens"]
            stats["cost_per_request"] = stats["total_cost"] / stats["total_requests"]
        else:
            stats["cost_per_token"] = 0.0
            stats["cost_per_request"] = 0.0
        
        return stats
    
    def reset_usage_stats(self):
        """Reset all usage statistics"""
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_latency_ms": 0.0,
            "provider_usage": {}
        }
        
        # Reset provider-specific stats
        for provider in self.provider_chain:
            self.usage_stats["provider_usage"][provider.provider_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "cost": 0.0,
                "tokens": 0,
                "latency_ms": 0.0
            }
        
        # Also reset each provider's internal stats
        for provider in self.provider_chain:
            provider.reset_usage_stats()
        
        logger.info("Reset all usage statistics")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [p.provider_name for p in self.provider_chain]
    
    def get_provider_info(self) -> Dict[str, Dict]:
        """Get detailed information about each provider"""
        info = {}
        for provider in self.provider_chain:
            provider_stats = self.usage_stats["provider_usage"][provider.provider_name]
            info[provider.provider_name] = {
                "config": {
                    "model": provider.config.model,
                    "base_url": provider.config.base_url,
                    "temperature": provider.config.temperature,
                    "max_tokens": provider.config.max_tokens,
                    "timeout": provider.config.timeout,
                },
                "stats": provider_stats,
                "internal_stats": provider.get_usage_stats()
            }
        return info