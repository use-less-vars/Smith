"""
Anthropic Claude provider implementation.
Supports Claude models with tool use .
"""
from typing import Dict, List, Any, Optional
import time
import json
import logging

import anthropic
from anthropic import APIError, RateLimitError

from .base import LLMProvider, ProviderConfig, LLMResponse
from .tool_converter import ToolFormatConverter
from .exceptions import ProviderError, RateLimitExceeded, AuthenticationError

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """
    Provider for Anthropic Claude API.
    Supports Claude 3 Opus, Sonnet, Haiku with tool use .
    """
    
    # Claude 3 pricing (per 1M tokens) - update as needed
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3.5-sonnet-20240620": {"input": 3.0, "output": 15.0},
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
        
        self.converter = ToolFormatConverter()
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute chat completion with Claude API"""
        start_time = time.time()
        
        try:
            # Convert messages to Anthropic format
            system_msg = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    # Map roles: user/assistant only
                    role = "user" if msg["role"] == "user" else "assistant"
                    anthropic_messages.append({
                        "role": role,
                        "content": msg["content"]
                    })
            
            # Prepare API kwargs
            api_kwargs = {
                "model": self.config.model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
                "temperature": kwargs.get("temperature", self.config.temperature),
                **kwargs
            }
            
            if system_msg:
                api_kwargs["system"] = system_msg
            
            # Add tools if provided
            if tools:
                api_kwargs["tools"] = self.converter.to_anthropic(tools)
            
            # Make API call
            response = self.client.messages.create(**api_kwargs)
            
            # Parse response
            llm_response = self.parse_response(response, start_time)
            
            # Track usage
            self.track_usage(llm_response)
            
            return llm_response
            
        except RateLimitError as e:
            raise RateLimitExceeded(f"Rate limit exceeded: {e}")
        except APIError as e:
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}")
            raise ProviderError(f"API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}")
    
    def parse_response(self, raw_response: Any, start_time: float) -> LLMResponse:
        """Parse Anthropic-specific response format """
        latency = (time.time() - start_time) * 1000
        
        # Extract content
        content = ""
        tool_calls = []
        
        for content_block in raw_response.content:
            if content_block.type == "text":
                content = content_block.text
            elif content_block.type == "tool_use":
                # Handle both dictionary and object tool calls
                if hasattr(content_block, 'name'):
                    # Object format (Anthropic SDK)
                    name = content_block.name
                    arguments = json.dumps(content_block.input)
                    cb_id = content_block.id
                else:
                    # Dictionary format
                    name = content_block.get("name")
                    arguments = json.dumps(content_block.get("input", {}))
                    cb_id = content_block.get("id")
                tool_calls.append({
                    "id": cb_id,
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": arguments
                    }
                })
        
        # Extract usage
        usage = {}
        if hasattr(raw_response, 'usage'):
            usage = {
                "prompt_tokens": raw_response.usage.input_tokens,
                "completion_tokens": raw_response.usage.output_tokens,
                "total_tokens": raw_response.usage.input_tokens + raw_response.usage.output_tokens
            }
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            raw_response=raw_response,
            provider="anthropic",
            model=self.config.model,
            latency_ms=latency
        )
    
    def count_tokens(self, messages: List[Dict], tools: Optional[List] = None) -> int:
        """
        Count tokens using Anthropic's token counting API .
        Falls back to estimation if API not available.
        """
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                if msg["role"] != "system":
                    anthropic_messages.append({
                        "role": "user" if msg["role"] == "user" else "assistant",
                        "content": msg["content"]
                    })
            
            # Use Anthropic's token counter
            response = self.client.beta.messages.count_tokens(
                model=self.config.model,
                messages=anthropic_messages
            )
            return response.input_tokens
            
        except Exception as e:
            logger.warning(f"Anthropic token counting failed: {e}")
            # Rough estimation: ~4 chars per token
            text = " ".join([m.get("content", "") for m in messages])
            return len(text) // 4
    
    def _calculate_cost(self, response: LLMResponse) -> float:
        """Calculate cost based on Claude pricing"""
        pricing = self.PRICING.get(self.config.model, self.PRICING["claude-3-haiku-20240307"])
        
        prompt_tokens = response.usage.get("prompt_tokens", 0)
        completion_tokens = response.usage.get("completion_tokens", 0)
        
        cost = (prompt_tokens * pricing["input"] / 1_000_000) + \
               (completion_tokens * pricing["output"] / 1_000_000)
        
        return cost
