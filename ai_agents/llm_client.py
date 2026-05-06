"""LLM API client abstraction.

Supports Anthropic Claude (primary) and OpenAI (fallback).
Lightweight wrapper for security advisory analysis.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM interface for security advisory analysis."""
    
    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.provider = None
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize LLM client with available provider."""
        if self.anthropic_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
                self.provider = "anthropic"
                logger.info("Using Anthropic Claude for advisory analysis")
            except ImportError:
                logger.warning("anthropic library not installed, trying OpenAI")
                self._try_openai()
        elif self.openai_key:
            self._try_openai()
        else:
            logger.warning("No LLM API key configured (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
            self.provider = None
    
    def _try_openai(self):
        """Try to initialize OpenAI client."""
        if self.openai_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.openai_key)
                self.provider = "openai"
                logger.info("Using OpenAI for advisory analysis")
            except ImportError:
                logger.warning("openai library not installed")
    
    def analyze(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Call LLM for advisory analysis.
        
        Args:
            prompt: The analysis request
            system_prompt: Optional system context
            
        Returns:
            LLM response or None if unavailable
        """
        if not self.client or not self.provider:
            logger.warning("LLM client not available, skipping advisory analysis")
            return None
        
        try:
            if self.provider == "anthropic":
                return self._call_anthropic(prompt, system_prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt, system_prompt)
        except Exception as e:
            logger.error(f"LLM API error ({self.provider}): {e}")
            return None
    
    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic Claude API."""
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt or "You are a security expert helping developers understand and fix vulnerabilities.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI GPT API."""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            system=system_prompt or "You are a security expert helping developers understand and fix vulnerabilities.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.provider is not None
