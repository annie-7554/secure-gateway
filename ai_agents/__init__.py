"""AI Security Advisory Layer - Lightweight, non-blocking analysis.

This module provides advisory-only security analysis. It does NOT enforce
anything. Deterministic security gates remain authoritative.
"""

from .security_advisor import SecurityAdvisor, create_advisor
from .findings_parser import FindingsParser, Finding
from .llm_client import LLMClient

__all__ = [
    "SecurityAdvisor",
    "create_advisor",
    "FindingsParser",
    "Finding",
    "LLMClient"
]
