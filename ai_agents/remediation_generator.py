"""Generate remediation guidance for security findings.

Uses LLM to provide developer-friendly fix recommendations.
"""

import json
import logging
from typing import Optional, Dict, Any
from .llm_client import LLMClient
from .advisor_prompts import (
    format_remediation_prompt,
    RISK_ASSESSMENT_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


class RemediationGenerator:
    """Generate remediation guidance using LLM."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
    
    def generate_remediation(self, title: str, severity: str, 
                            description: str) -> Dict[str, Any]:
        """
        Generate remediation steps for a finding.
        
        Args:
            title: Finding title/ID
            severity: Severity level
            description: Finding description
            
        Returns:
            Dictionary with remediation guidance
        """
        if not self.llm.is_available():
            logger.warning("LLM not available, returning basic remediation")
            return self._fallback_remediation(title, severity)
        
        prompt = format_remediation_prompt(title, severity, description)
        
        try:
            response = self.llm.analyze(
                prompt=prompt,
                system_prompt=RISK_ASSESSMENT_SYSTEM_PROMPT
            )
            
            if not response:
                return self._fallback_remediation(title, severity)
            
            # Try to parse as structured data
            return {
                "title": title,
                "severity": severity,
                "guidance": response,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error generating remediation: {e}")
            return self._fallback_remediation(title, severity)
    
    def _fallback_remediation(self, title: str, severity: str) -> Dict[str, Any]:
        """Return basic remediation when LLM unavailable."""
        actions = {
            "CRITICAL": "Address immediately - critical security issue",
            "HIGH": "Fix before next deployment",
            "MEDIUM": "Plan fix in current sprint",
            "LOW": "Address when possible"
        }
        
        return {
            "title": title,
            "severity": severity,
            "guidance": actions.get(severity, "See scanner output for details"),
            "status": "fallback"
        }
    
    def generate_summary(self, findings_list: list) -> str:
        """
        Generate a summary of all findings.
        
        Args:
            findings_list: List of Finding objects
            
        Returns:
            Summary string
        """
        if not findings_list:
            return "No security findings detected."
        
        # Count by severity
        counts = {}
        for finding in findings_list:
            severity = finding.severity
            counts[severity] = counts.get(severity, 0) + 1
        
        # Build summary
        summary_parts = []
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if severity in counts:
                summary_parts.append(f"{counts[severity]} {severity.lower()}")
        
        return f"Found {', '.join(summary_parts)} severity findings."
