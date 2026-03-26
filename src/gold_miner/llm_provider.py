"""LLM Provider management with automatic failover support."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dotenv import load_dotenv

from .llm import AnthropicClient, OpenAICompatibleClient, LLMError


class ProviderStatus(Enum):
    """Provider status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class LLMProviderConfig:
    """Configuration for a single LLM provider."""
    name: str
    base_url: str
    api_key: str
    model: str
    priority: int  # Lower number = higher priority
    timeout: int = 60
    is_anthropic: bool = False  # True for Anthropic API format


@dataclass
class ProviderHealth:
    """Health status for a provider."""
    status: ProviderStatus
    consecutive_failures: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]


class LLMProvider:
    """Individual LLM provider wrapper with health tracking."""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0,
            last_failure_time=None,
            last_success_time=time.time()
        )
        self._client: Optional[Any] = None
    
    def get_client(self) -> Any:
        """Get or create the LLM client."""
        if self._client is None:
            if self.config.is_anthropic:
                self._client = AnthropicClient(
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    model=self.config.model,
                    timeout=self.config.timeout,
                    enable_circuit_breaker=True
                )
            else:
                self._client = OpenAICompatibleClient(
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    model=self.config.model,
                    timeout=self.config.timeout,
                    enable_circuit_breaker=True
                )
        return self._client
    
    def record_success(self):
        """Record a successful request."""
        self.health.consecutive_failures = 0
        self.health.last_success_time = time.time()
        if self.health.status == ProviderStatus.UNHEALTHY:
            self.health.status = ProviderStatus.DEGRADED
    
    def record_failure(self):
        """Record a failed request."""
        self.health.consecutive_failures += 1
        self.health.last_failure_time = time.time()
        
        # Mark as degraded after 3 failures
        if self.health.consecutive_failures >= 3:
            self.health.status = ProviderStatus.DEGRADED
        
        # Mark as unhealthy after 5 failures
        if self.health.consecutive_failures >= 5:
            self.health.status = ProviderStatus.UNHEALTHY
    
    def is_available(self) -> bool:
        """Check if provider is available for use."""
        if self.health.status == ProviderStatus.HEALTHY:
            return True
        
        # If degraded, wait 30 seconds before retry
        if self.health.status == ProviderStatus.DEGRADED:
            if self.health.last_failure_time:
                elapsed = time.time() - self.health.last_failure_time
                return elapsed > 30
        
        # If unhealthy, wait 5 minutes before retry
        if self.health.status == ProviderStatus.UNHEALTHY:
            if self.health.last_failure_time:
                elapsed = time.time() - self.health.last_failure_time
                return elapsed > 300
        
        return False
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat request through this provider."""
        client = self.get_client()
        return client.chat(messages, **kwargs)


class LLMProviderManager:
    """Manager for multiple LLM providers with automatic failover."""
    
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self.providers: List[LLMProvider] = []
        self._load_providers_from_env()
    
    def _load_providers_from_env(self):
        """Load all LLM providers from environment variables.
        
        Supports two naming conventions:
        1. LLM_BASE_URL, LLM_BASE_URL_backup1, LLM_BASE_URL_backup2
        2. ANTHROPIC_BASE_URL, OPENAI_BASE_URL, DASHSCOPE_BASE_URL
        """
        providers_config = []
        
        # Helper function to get env var with fallback
        def get_env(key, default=None):
            return os.getenv(key, default)
        
        # Primary provider (highest priority) - try LLM_BASE_URL first, then ANTHROPIC
        primary_url = get_env("LLM_BASE_URL") or get_env("ANTHROPIC_BASE_URL")
        if primary_url:
            providers_config.append(LLMProviderConfig(
                name="primary",
                base_url=primary_url,
                api_key=get_env("LLM_API_KEY") or get_env("ANTHROPIC_API_KEY", ""),
                model=get_env("LLM_MODEL") or get_env("ANTHROPIC_MODEL", ""),
                priority=1,
                timeout=int(get_env("LLM_TIMEOUT") or "60"),
                is_anthropic="anthropic" in primary_url.lower() or 
                            "claude" in (get_env("LLM_MODEL") or get_env("ANTHROPIC_MODEL", "")).lower() or
                            "/messages" in primary_url.lower()
            ))
        
        # Backup 1 - try LLM_BASE_URL_backup1 first, then OPENAI
        backup1_url = get_env("LLM_BASE_URL_backup1") or get_env("OPENAI_BASE_URL")
        if backup1_url:
            providers_config.append(LLMProviderConfig(
                name="backup1",
                base_url=backup1_url,
                api_key=get_env("LLM_API_KEY_backup1") or get_env("OPENAI_API_KEY", ""),
                model=get_env("LLM_MODEL_backup1") or get_env("OPENAI_MODEL", ""),
                priority=2,
                timeout=int(get_env("LLM_TIMEOUT_backup1") or "60"),
                is_anthropic="anthropic" in backup1_url.lower() or
                            "claude" in (get_env("LLM_MODEL_backup1") or get_env("OPENAI_MODEL", "")).lower()
            ))
        
        # Backup 2 - try LLM_BASE_URL_backup2 first, then DASHSCOPE
        backup2_url = get_env("LLM_BASE_URL_backup2") or get_env("DASHSCOPE_BASE_URL")
        if backup2_url:
            providers_config.append(LLMProviderConfig(
                name="backup2",
                base_url=backup2_url,
                api_key=get_env("LLM_API_KEY_backup2") or get_env("DASHSCOPE_API_KEY", ""),
                model=get_env("LLM_MODEL_backup2") or get_env("DASHSCOPE_MODEL", ""),
                priority=3,
                timeout=int(get_env("LLM_TIMEOUT_backup2") or "60"),
                is_anthropic="anthropic" in backup2_url.lower() or
                            "claude" in (get_env("LLM_MODEL_backup2") or get_env("DASHSCOPE_MODEL", "")).lower()
            ))
        
        # Sort by priority
        providers_config.sort(key=lambda x: x.priority)
        
        for config in providers_config:
            self.providers.append(LLMProvider(config))
            print(f"[LLM Provider] Registered: {config.name} (priority={config.priority}, model={config.model})")
        
        if not self.providers:
            raise ValueError("No LLM providers configured. Please set LLM_BASE_URL in .env")
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers sorted by priority."""
        available = [p for p in self.providers if p.is_available()]
        return sorted(available, key=lambda p: p.config.priority)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        enforce_json: bool = False,
        max_retries_per_provider: int = 3,
        **kwargs
    ) -> str:
        """
        Send chat request with automatic failover.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            enforce_json: Whether to enforce JSON output
            max_retries_per_provider: Max retries per provider before failover
            **kwargs: Additional arguments
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If all providers fail
        """
        last_error = None
        attempted_providers = []
        
        # Get available providers
        available_providers = self.get_available_providers()
        
        if not available_providers:
            # If no providers available, try all providers regardless of health
            available_providers = self.providers
            print("[LLM Provider Manager] Warning: No healthy providers, trying all...")
        
        for provider in available_providers:
            attempted_providers.append(provider.config.name)
            
            for attempt in range(max_retries_per_provider):
                try:
                    print(f"[LLM Provider Manager] Trying {provider.config.name} (attempt {attempt + 1}/{max_retries_per_provider})...")
                    
                    response = provider.chat(
                        messages,
                        temperature=temperature,
                        enforce_json=enforce_json,
                        retries=0,  # We handle retries here
                        **kwargs
                    )
                    
                    # Success!
                    provider.record_success()
                    print(f"[LLM Provider Manager] Success with {provider.config.name}")
                    return response
                    
                except Exception as e:
                    last_error = e
                    print(f"[LLM Provider Manager] {provider.config.name} failed (attempt {attempt + 1}): {e}")
                    
                    if attempt < max_retries_per_provider - 1:
                        # Exponential backoff
                        wait_time = 1.0 * (2 ** attempt)
                        time.sleep(wait_time)
            
            # All retries failed for this provider
            provider.record_failure()
            print(f"[LLM Provider Manager] {provider.config.name} marked as {provider.health.status.value}")
        
        # All providers failed
        error_msg = f"All LLM providers failed after retries. Attempted: {', '.join(attempted_providers)}. Last error: {last_error}"
        print(f"[LLM Provider Manager] {error_msg}")
        raise LLMError(error_msg)
    
    def get_provider_status(self) -> List[Dict[str, Any]]:
        """Get status of all providers."""
        return [
            {
                "name": p.config.name,
                "model": p.config.model,
                "priority": p.config.priority,
                "status": p.health.status.value,
                "consecutive_failures": p.health.consecutive_failures,
                "available": p.is_available()
            }
            for p in self.providers
        ]


# Global provider manager instance
_provider_manager: Optional[LLMProviderManager] = None


def get_provider_manager() -> LLMProviderManager:
    """Get or create the global provider manager."""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = LLMProviderManager()
    return _provider_manager


def reset_provider_manager():
    """Reset the provider manager (useful for testing)."""
    global _provider_manager
    _provider_manager = None
