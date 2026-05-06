#!/usr/bin/env python3
"""Local script to test the security advisor with sample findings."""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents import (
    SecurityAdvisor,
    FindingsParser,
    Finding
)


def test_advisor_with_semgrep_findings():
    """Test advisor with Semgrep findings."""
    print("\n" + "="*70)
    print("TEST 1: Semgrep SAST Findings")
    print("="*70)
    
    semgrep_json = json.dumps({
        "results": [
            {
                "check_id": "python.django.security.injection.sql.sql-query-string-formatting",
                "severity": "ERROR",
                "extra": {
                    "message": "User input in SQL query - SQL injection risk",
                    "fix": "Use parameterized queries with placeholders"
                }
            },
            {
                "check_id": "python.cryptography.security.insecure-hash-functions.insecure-hash-md5",
                "severity": "WARNING",
                "extra": {
                    "message": "MD5 is cryptographically broken",
                    "fix": "Use SHA256 or bcrypt for hashing"
                }
            }
        ]
    })
    
    findings = FindingsParser.parse_semgrep(semgrep_json)
    print(f"Parsed {len(findings)} findings from Semgrep")
    
    # Analyze with advisor
    advisor = SecurityAdvisor()
    assessment = advisor.analyze_findings(findings)
    
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Summary: {assessment.summary}")
    print(f"Recommended Action: {assessment.recommended_action}")
    
    # Generate PR comment
    comment = advisor.generate_pr_comment(assessment, "FAIL")
    print("\nGenerated PR Comment:")
    print(comment)


def test_advisor_with_snyk_findings():
    """Test advisor with Snyk dependency findings."""
    print("\n" + "="*70)
    print("TEST 2: Snyk Dependency Findings")
    print("="*70)
    
    snyk_json = json.dumps({
        "vulnerabilities": [
            {
                "package": "requests",
                "version": "2.25.0",
                "severity": "high",
                "title": "Connection pool race condition (CVE-2021-3737)",
                "fixedIn": ["2.28.1"]
            },
            {
                "package": "flask",
                "version": "1.1.2",
                "severity": "medium",
                "title": "Open redirect vulnerability",
                "fixedIn": ["2.0.0"]
            }
        ]
    })
    
    findings = FindingsParser.parse_snyk(snyk_json)
    print(f"Parsed {len(findings)} findings from Snyk")
    
    advisor = SecurityAdvisor()
    assessment = advisor.analyze_findings(findings)
    
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Summary: {assessment.summary}")
    print(f"Recommended Action: {assessment.recommended_action}")
    
    comment = advisor.generate_pr_comment(assessment, "FAIL")
    print("\nGenerated PR Comment:")
    print(comment)


def test_advisor_with_trivy_findings():
    """Test advisor with Trivy container findings."""
    print("\n" + "="*70)
    print("TEST 3: Trivy Container Image Findings")
    print("="*70)
    
    trivy_json = json.dumps({
        "Results": [
            {
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2021-22911",
                        "Title": "OpenSSL vulnerability",
                        "Severity": "CRITICAL",
                        "Description": "High severity OpenSSL vulnerability",
                        "FixedVersion": "1.1.1k"
                    },
                    {
                        "VulnerabilityID": "CVE-2021-3156",
                        "Title": "sudo heap-based buffer overflow",
                        "Severity": "HIGH",
                        "Description": "Privilege escalation vulnerability",
                        "FixedVersion": "1.9.6p1"
                    }
                ]
            }
        ]
    })
    
    findings = FindingsParser.parse_trivy(trivy_json)
    print(f"Parsed {len(findings)} findings from Trivy")
    
    advisor = SecurityAdvisor()
    assessment = advisor.analyze_findings(findings)
    
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Summary: {assessment.summary}")
    print(f"Recommended Action: {assessment.recommended_action}")
    
    # Test deployment context
    deployment_context = advisor.generate_deployment_context(findings)
    print("\nDeployment Context:")
    print(deployment_context)


def test_advisor_graceful_degradation():
    """Test advisor graceful degradation with no findings."""
    print("\n" + "="*70)
    print("TEST 4: Graceful Degradation - No Findings")
    print("="*70)
    
    advisor = SecurityAdvisor()
    assessment = advisor.analyze_findings([])
    
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Summary: {assessment.summary}")
    print(f"Recommended Action: {assessment.recommended_action}")
    
    comment = advisor.generate_pr_comment(assessment, "PASS")
    print("\nGenerated PR Comment:")
    print(comment)


def test_severity_counting():
    """Test findings counting and prioritization."""
    print("\n" + "="*70)
    print("TEST 5: Findings Counting & Prioritization")
    print("="*70)
    
    findings = [
        Finding("tool1", "LOW", "Low priority", "Low description"),
        Finding("tool1", "CRITICAL", "Critical issue", "Critical description"),
        Finding("tool1", "MEDIUM", "Medium issue", "Medium description"),
        Finding("tool1", "HIGH", "High priority", "High description"),
        Finding("tool1", "HIGH", "Another high", "High description 2"),
    ]
    
    parser = FindingsParser()
    
    # Count
    counts = parser.count_by_severity(findings)
    print(f"Severity counts: {counts}")
    
    # Prioritize
    prioritized = parser.prioritize_findings(findings)
    print(f"\nPrioritized order:")
    for i, f in enumerate(prioritized, 1):
        print(f"  {i}. [{f.severity}] {f.title}")


if __name__ == "__main__":
    print("\n🔐 Security Advisor Local Testing")
    print("=" * 70)
    print("Testing AI security advisory layer with sample findings...")
    
    try:
        test_advisor_with_semgrep_findings()
        test_advisor_with_snyk_findings()
        test_advisor_with_trivy_findings()
        test_advisor_graceful_degradation()
        test_severity_counting()
        
        print("\n" + "="*70)
        print("✅ All advisor tests completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
