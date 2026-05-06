"""Tests for security advisor (mocked LLM, no API calls needed)."""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock

from ai_agents import (
    SecurityAdvisor, 
    FindingsParser,
    Finding,
    LLMClient
)


class TestFindingsParser(unittest.TestCase):
    """Test findings parser with various formats."""
    
    def test_parse_semgrep_findings(self):
        """Test Semgrep JSON parsing."""
        semgrep_json = json.dumps({
            "results": [
                {
                    "check_id": "sql-injection",
                    "severity": "ERROR",
                    "extra": {
                        "message": "Potential SQL injection vulnerability",
                        "fix": "Use parameterized queries"
                    }
                }
            ]
        })
        
        findings = FindingsParser.parse_semgrep(semgrep_json)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tool, "semgrep")
        self.assertEqual(findings[0].severity, "HIGH")
        self.assertEqual(findings[0].title, "sql-injection")
    
    def test_parse_snyk_findings(self):
        """Test Snyk JSON parsing."""
        snyk_json = json.dumps({
            "vulnerabilities": [
                {
                    "package": "requests",
                    "version": "2.25.0",
                    "severity": "high",
                    "title": "Connection pool race condition",
                    "fixedIn": ["2.28.1"]
                }
            ]
        })
        
        findings = FindingsParser.parse_snyk(snyk_json)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tool, "snyk")
        self.assertEqual(findings[0].severity, "HIGH")
        self.assertIn("requests", findings[0].title)
    
    def test_count_by_severity(self):
        """Test counting findings by severity."""
        findings = [
            Finding("tool1", "CRITICAL", "Crit1", "Desc"),
            Finding("tool1", "HIGH", "High1", "Desc"),
            Finding("tool1", "HIGH", "High2", "Desc"),
            Finding("tool1", "LOW", "Low1", "Desc"),
        ]
        
        counts = FindingsParser.count_by_severity(findings)
        
        self.assertEqual(counts["CRITICAL"], 1)
        self.assertEqual(counts["HIGH"], 2)
        self.assertEqual(counts["LOW"], 1)
    
    def test_prioritize_findings(self):
        """Test findings prioritization by severity."""
        findings = [
            Finding("tool1", "LOW", "Low1", "Desc"),
            Finding("tool1", "CRITICAL", "Crit1", "Desc"),
            Finding("tool1", "MEDIUM", "Med1", "Desc"),
        ]
        
        prioritized = FindingsParser.prioritize_findings(findings)
        
        self.assertEqual(prioritized[0].severity, "CRITICAL")
        self.assertEqual(prioritized[1].severity, "MEDIUM")
        self.assertEqual(prioritized[2].severity, "LOW")


class TestSecurityAdvisor(unittest.TestCase):
    """Test security advisor (with mocked LLM)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.advisor = SecurityAdvisor()
        # Mock the LLM client
        self.advisor.llm = Mock(spec=LLMClient)
        self.advisor.llm.is_available.return_value = False  # Start with LLM unavailable
    
    def test_analyze_empty_findings(self):
        """Test analysis with no findings."""
        assessment = self.advisor.analyze_findings([])
        
        self.assertEqual(assessment.risk_level, "low risk")
        self.assertIn("No security findings", assessment.summary)
    
    def test_analyze_findings_without_llm(self):
        """Test analysis when LLM is unavailable."""
        findings = [
            Finding("semgrep", "CRITICAL", "SQL Injection", "Unsafe query"),
            Finding("snyk", "HIGH", "Dependency Vuln", "Old package"),
        ]
        
        assessment = self.advisor.analyze_findings(findings)
        
        self.assertEqual(assessment.risk_level, "high risk")
        self.assertIn("critical", assessment.summary)
        self.assertIn("fix immediately", assessment.recommended_action)
    
    def test_analyze_findings_with_llm(self):
        """Test analysis when LLM is available."""
        findings = [
            Finding("semgrep", "MEDIUM", "Weak Crypto", "Using MD5"),
        ]
        
        # Mock LLM response
        mock_response = json.dumps({
            "risk_level": "moderate risk",
            "summary": "Found weak cryptography usage",
            "findings": [{"severity": "MEDIUM", "title": "Weak Crypto"}],
            "recommended_action": "fix in current sprint"
        })
        
        self.advisor.llm.is_available.return_value = True
        self.advisor.llm.analyze.return_value = mock_response
        
        assessment = self.advisor.analyze_findings(findings)
        
        self.assertEqual(assessment.risk_level, "moderate risk")
        self.assertIn("weak cryptography", assessment.summary)
    
    def test_pr_comment_generation(self):
        """Test PR comment generation."""
        from ai_agents.security_advisor import RiskAssessment
        
        assessment = RiskAssessment(
            risk_level="moderate risk",
            summary="Found 2 HIGH severity issues",
            findings=[{"severity": "HIGH", "title": "Issue 1"}],
            recommended_action="fix before deployment"
        )
        
        comment = self.advisor.generate_pr_comment(assessment, "FAIL")
        
        self.assertIn("Security Advisory", comment)
        self.assertIn("moderate risk", comment)
        self.assertIn("fix before deployment", comment)
        self.assertIn("FAIL", comment)
    
    def test_deployment_context_generation(self):
        """Test deployment context assessment."""
        findings = [
            Finding("trivy", "HIGH", "CVE-2021-1234", "Container vuln"),
        ]
        
        context = self.advisor.generate_deployment_context(findings)
        
        self.assertIn("Deployment Security Context", context)
        self.assertIn("Moderate Risk", context)


class TestGracefulDegradation(unittest.TestCase):
    """Test graceful degradation when services fail."""
    
    def test_advisor_works_without_llm(self):
        """Test advisor provides fallback when LLM unavailable."""
        advisor = SecurityAdvisor()
        
        # Simulate LLM unavailable
        advisor.llm.is_available = Mock(return_value=False)
        
        findings = [
            Finding("semgrep", "HIGH", "Issue1", "Desc"),
        ]
        
        assessment = advisor.analyze_findings(findings)
        
        # Should still provide assessment
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.risk_level, "moderate risk")
        self.assertIn("high", assessment.summary)
    
    def test_malformed_llm_response(self):
        """Test handling of malformed LLM responses."""
        advisor = SecurityAdvisor()
        advisor.llm = Mock(spec=LLMClient)
        advisor.llm.is_available.return_value = True
        advisor.llm.analyze.return_value = "Not JSON at all!"
        
        findings = [
            Finding("semgrep", "MEDIUM", "Issue1", "Desc"),
        ]
        
        assessment = advisor.analyze_findings(findings)
        
        # Should fall back to basic assessment
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.risk_level, "low risk")


class TestSecurityAdvisorIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""
    
    def test_end_to_end_analysis_and_comment(self):
        """Test complete flow from findings to PR comment."""
        advisor = SecurityAdvisor()
        advisor.llm.is_available = Mock(return_value=False)
        
        # Parse findings
        semgrep_json = json.dumps({
            "results": [
                {
                    "check_id": "weak-crypto",
                    "severity": "WARNING",
                    "extra": {"message": "Using MD5 for hashing"}
                }
            ]
        })
        
        findings = FindingsParser.parse_semgrep(semgrep_json)
        
        # Analyze
        assessment = advisor.analyze_findings(findings)
        
        # Generate comment
        comment = advisor.generate_pr_comment(assessment, "FAIL")
        
        # Verify complete flow
        self.assertIsNotNone(findings)
        self.assertIsNotNone(assessment)
        self.assertIn("Security Advisory", comment)
        self.assertIn("FAIL", comment)


if __name__ == "__main__":
    unittest.main()
