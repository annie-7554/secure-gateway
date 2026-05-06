"""Parse security findings from SARIF and JSON formats.

Extracts and normalizes findings from different security scanners.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Finding:
    """Represents a security finding."""
    
    def __init__(self, tool: str, severity: str, title: str, description: str, 
                 remediation: Optional[str] = None):
        self.tool = tool
        self.severity = severity.upper()
        self.title = title
        self.description = description
        self.remediation = remediation or ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "remediation": self.remediation
        }


class FindingsParser:
    """Parse security findings from various formats."""
    
    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    
    @staticmethod
    def parse_sarif(sarif_json: str) -> List[Finding]:
        """Parse SARIF format findings (used by Semgrep, Trivy, etc.)."""
        findings = []
        try:
            data = json.loads(sarif_json)
            for run in data.get("runs", []):
                tool_name = run.get("tool", {}).get("driver", {}).get("name", "unknown")
                for result in run.get("results", []):
                    level = result.get("level", "warning").upper()
                    # Map SARIF levels to standard severities
                    severity = FindingsParser._map_level_to_severity(level)
                    
                    message = result.get("message", {})
                    title = message.get("text", "Unknown issue")
                    
                    finding = Finding(
                        tool=tool_name,
                        severity=severity,
                        title=title,
                        description=FindingsParser._extract_description(result)
                    )
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SARIF JSON: {e}")
        
        return findings
    
    @staticmethod
    def parse_semgrep(semgrep_json: str) -> List[Finding]:
        """Parse Semgrep JSON findings."""
        findings = []
        try:
            data = json.loads(semgrep_json)
            for result in data.get("results", []):
                severity = FindingsParser._map_semgrep_severity(
                    result.get("severity", "WARNING")
                )
                
                finding = Finding(
                    tool="semgrep",
                    severity=severity,
                    title=result.get("check_id", "unknown"),
                    description=result.get("extra", {}).get("message", ""),
                    remediation=result.get("extra", {}).get("fix", "")
                )
                findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep JSON: {e}")
        
        return findings
    
    @staticmethod
    def parse_snyk(snyk_json: str) -> List[Finding]:
        """Parse Snyk JSON findings."""
        findings = []
        try:
            data = json.loads(snyk_json)
            
            # Process vulnerabilities
            for vuln in data.get("vulnerabilities", []):
                severity = vuln.get("severity", "low").upper()
                
                finding = Finding(
                    tool="snyk",
                    severity=severity,
                    title=f"{vuln.get('package', 'unknown')}@{vuln.get('version', '?')}",
                    description=vuln.get("title", "Dependency vulnerability"),
                    remediation=vuln.get("fixedIn", ["No fix available"])[0]
                )
                findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Snyk JSON: {e}")
        
        return findings
    
    @staticmethod
    def parse_trivy(trivy_json: str) -> List[Finding]:
        """Parse Trivy JSON findings."""
        findings = []
        try:
            data = json.loads(trivy_json)
            
            for result in data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []):
                    severity = vuln.get("Severity", "UNKNOWN").upper()
                    
                    finding = Finding(
                        tool="trivy",
                        severity=severity,
                        title=vuln.get("VulnerabilityID", "unknown"),
                        description=vuln.get("Title", vuln.get("Description", "")),
                        remediation=vuln.get("FixedVersion", "")
                    )
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Trivy JSON: {e}")
        
        return findings
    
    @staticmethod
    def _map_level_to_severity(level: str) -> str:
        """Map SARIF level to standard severity."""
        mapping = {
            "ERROR": "HIGH",
            "WARNING": "MEDIUM",
            "NOTE": "LOW",
            "NONE": "INFO"
        }
        return mapping.get(level, level)
    
    @staticmethod
    def _map_semgrep_severity(severity: str) -> str:
        """Map Semgrep severity to standard."""
        mapping = {
            "ERROR": "HIGH",
            "WARNING": "MEDIUM",
            "INFO": "LOW"
        }
        return mapping.get(severity, severity)
    
    @staticmethod
    def _extract_description(result: Dict[str, Any]) -> str:
        """Extract description from SARIF result."""
        # Try various fields where description might be
        if "message" in result:
            msg = result["message"]
            if isinstance(msg, dict):
                return msg.get("text", "")
            return str(msg)
        
        if "ruleId" in result:
            return f"Rule violation: {result['ruleId']}"
        
        return "Unknown issue"
    
    @staticmethod
    def prioritize_findings(findings: List[Finding]) -> List[Finding]:
        """Sort findings by severity."""
        return sorted(
            findings,
            key=lambda f: FindingsParser.SEVERITY_ORDER.get(f.severity, 999)
        )
    
    @staticmethod
    def group_by_severity(findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by severity level."""
        grouped = {}
        for finding in findings:
            if finding.severity not in grouped:
                grouped[finding.severity] = []
            grouped[finding.severity].append(finding)
        return grouped
    
    @staticmethod
    def count_by_severity(findings: List[Finding]) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {level: 0 for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}
        for finding in findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts
