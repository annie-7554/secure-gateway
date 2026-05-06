"""Security Advisory - AI-assisted vulnerability analysis and guidance.

Analyzes security findings and provides developer-friendly risk assessment
and remediation guidance. Advisory layer only - does not enforce anything.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .llm_client import LLMClient
from .findings_parser import FindingsParser, Finding
from .remediation_generator import RemediationGenerator
from .advisor_prompts import (
    format_risk_assessment_prompt,
    format_deployment_context_prompt,
    RISK_ASSESSMENT_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Risk assessment result from advisor."""
    risk_level: str  # low risk, moderate risk, high risk
    summary: str
    findings: List[Dict[str, Any]]
    recommended_action: str


class SecurityAdvisor:
    """AI-powered security advisory layer (advisory only, non-blocking)."""
    
    def __init__(self):
        self.llm = LLMClient()
        self.parser = FindingsParser()
        self.remediation = RemediationGenerator(self.llm)
    
    def analyze_findings(self, findings: List[Finding]) -> RiskAssessment:
        """
        Analyze security findings and provide risk assessment.
        
        This is an advisory analysis only - it does not enforce anything.
        The pipeline still respects deterministic gate decisions.
        
        Args:
            findings: List of Finding objects
            
        Returns:
            RiskAssessment with risk level, summary, and guidance
        """
        if not findings:
            return RiskAssessment(
                risk_level="low risk",
                summary="No security findings detected.",
                findings=[],
                recommended_action="proceed"
            )
        
        # Prioritize and group findings
        prioritized = self.parser.prioritize_findings(findings)
        counts = self.parser.count_by_severity(findings)
        
        # Generate findings text for LLM
        findings_text = self._format_findings_for_analysis(prioritized, counts)
        
        # Get LLM analysis if available
        assessment = self._get_llm_assessment(findings_text)
        
        # If LLM unavailable, provide basic assessment
        if not assessment:
            assessment = self._basic_assessment(prioritized, counts)
        
        return assessment
    
    def _format_findings_for_analysis(self, findings: List[Finding], 
                                      counts: Dict[str, int]) -> str:
        """Format findings for LLM analysis."""
        lines = [
            f"Security Findings Summary:",
            f"- CRITICAL: {counts.get('CRITICAL', 0)}",
            f"- HIGH: {counts.get('HIGH', 0)}",
            f"- MEDIUM: {counts.get('MEDIUM', 0)}",
            f"- LOW: {counts.get('LOW', 0)}",
            "",
            "Findings:"
        ]
        
        for finding in findings[:10]:  # Limit to top 10 for analysis
            lines.append(f"- [{finding.severity}] {finding.title}")
            if finding.description:
                lines.append(f"  {finding.description[:200]}")
        
        return "\n".join(lines)
    
    def _get_llm_assessment(self, findings_text: str) -> Optional[RiskAssessment]:
        """Get LLM risk assessment."""
        if not self.llm.is_available():
            return None
        
        prompt = format_risk_assessment_prompt(findings_text)
        
        try:
            response = self.llm.analyze(
                prompt=prompt,
                system_prompt=RISK_ASSESSMENT_SYSTEM_PROMPT
            )
            
            if not response:
                return None
            
            # Try to extract JSON from response
            assessment = self._parse_assessment_response(response)
            return assessment
        except Exception as e:
            logger.error(f"Error getting LLM assessment: {e}")
            return None
    
    def _parse_assessment_response(self, response: str) -> Optional[RiskAssessment]:
        """Parse LLM assessment response."""
        try:
            # Try to extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                risk_level = data.get("risk_level", "moderate risk")
                summary = data.get("summary", "See findings above")
                recommended = data.get("recommended_action", "review")
                
                return RiskAssessment(
                    risk_level=risk_level,
                    summary=summary,
                    findings=data.get("findings", []),
                    recommended_action=recommended
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse assessment JSON: {e}")
        
        return None
    
    def _basic_assessment(self, findings: List[Finding], 
                         counts: Dict[str, int]) -> RiskAssessment:
        """Provide basic assessment when LLM unavailable."""
        # Determine risk level based on findings
        if counts.get("CRITICAL", 0) > 0:
            risk_level = "high risk"
            recommended_action = "fix immediately"
        elif counts.get("HIGH", 0) > 0:
            risk_level = "moderate risk"
            recommended_action = "fix before deployment"
        else:
            risk_level = "low risk"
            recommended_action = "review and fix as scheduled"
        
        summary = self.remediation.generate_summary(findings)
        
        return RiskAssessment(
            risk_level=risk_level,
            summary=summary,
            findings=[f.to_dict() for f in findings[:5]],
            recommended_action=recommended_action
        )
    
    def generate_pr_comment(self, assessment: RiskAssessment, 
                           gate_status: str) -> str:
        """
        Generate PR comment with security advisory.
        
        Args:
            assessment: RiskAssessment from analyze_findings
            gate_status: Status from deterministic gate (PASS/FAIL)
            
        Returns:
            Markdown-formatted PR comment
        """
        comment_lines = [
            "🤖 **Security Advisory**",
            "",
            f"**Risk Assessment:** {assessment.risk_level}",
            f"**Gate Status:** {gate_status}",
            ""
        ]
        
        comment_lines.append(f"**Summary:** {assessment.summary}")
        comment_lines.append("")
        
        if assessment.findings:
            comment_lines.append("**Key Findings:**")
            for finding in assessment.findings[:5]:
                if isinstance(finding, dict):
                    comment_lines.append(
                        f"- [{finding.get('severity', 'MEDIUM')}] "
                        f"{finding.get('title', 'Unknown')}"
                    )
                else:
                    comment_lines.append(f"- {finding}")
            comment_lines.append("")
        
        comment_lines.append(f"**Recommended Action:** {assessment.recommended_action}")
        comment_lines.append("")
        comment_lines.append(
            "*This is an advisory assessment. Security gates make the final decision.*"
        )
        
        return "\n".join(comment_lines)
    
    def generate_deployment_context(self, findings: List[Finding]) -> str:
        """
        Generate deployment context assessment.
        
        Args:
            findings: List of findings for deployment
            
        Returns:
            Deployment context summary
        """
        if not findings:
            return "✅ No security concerns detected for deployment."
        
        counts = self.parser.count_by_severity(findings)
        
        context = [
            "**Deployment Security Context:**",
            ""
        ]
        
        # Determine risk level
        if counts.get("CRITICAL", 0) > 0:
            context.append("🔴 **High Risk** - Critical vulnerabilities present")
        elif counts.get("HIGH", 0) > 0:
            context.append("🟠 **Moderate Risk** - High severity vulnerabilities present")
        else:
            context.append("🟢 **Low Risk** - No critical vulnerabilities")
        
        context.append("")
        context.append(f"Findings: {self.remediation.generate_summary(findings)}")
        context.append("")
        context.append("*Deployment gates enforce policy; this is advisory context.*")
        
        return "\n".join(context)


def create_advisor() -> SecurityAdvisor:
    """Create a security advisor instance."""
    return SecurityAdvisor()
