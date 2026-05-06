#!/usr/bin/env python3
"""
GitHub Actions CLI for AI security advisor.

Integrates with Gate 1, 2, and 3 workflows to analyze findings
and post PR comments or workflow summaries.
"""

import json
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents import SecurityAdvisor, FindingsParser, Finding

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def load_sarif_file(filepath: str) -> list:
    """Load and parse SARIF file."""
    try:
        with open(filepath) as f:
            data = json.load(f)
        
        findings = []
        for run in data.get("runs", []):
            tool_name = run.get("tool", {}).get("driver", {}).get("name", "unknown")
            
            for result in run.get("results", []):
                level = result.get("level", "warning").upper()
                message = result.get("message", {})
                text = message.get("text", "Unknown issue")
                
                severity_map = {
                    "ERROR": "HIGH",
                    "WARNING": "MEDIUM",
                    "NOTE": "LOW"
                }
                severity = severity_map.get(level, level)
                
                finding = Finding(
                    tool=tool_name,
                    severity=severity,
                    title=result.get("ruleId", text),
                    description=text
                )
                findings.append(finding)
        
        logger.info(f"Loaded {len(findings)} findings from {filepath}")
        return findings
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {filepath}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="AI Security Advisor - GitHub Actions integration"
    )
    parser.add_argument(
        "--semgrep-sarif",
        help="Path to Semgrep SARIF file"
    )
    parser.add_argument(
        "--trivy-sarif",
        help="Path to Trivy SARIF file"
    )
    parser.add_argument(
        "--gate",
        choices=["gate1", "gate2", "gate3"],
        required=True,
        help="Which gate this is for"
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        help="Pull request number (for PR comments)"
    )
    parser.add_argument(
        "--output-comment",
        help="Output file for PR comment"
    )
    parser.add_argument(
        "--output-summary",
        help="Output file for workflow summary"
    )
    
    args = parser.parse_args()
    
    # Parse findings
    findings = []
    
    if args.semgrep_sarif:
        findings.extend(load_sarif_file(args.semgrep_sarif))
    
    if args.trivy_sarif:
        findings.extend(load_sarif_file(args.trivy_sarif))
    
    if not findings:
        logger.info("No findings detected")
    else:
        logger.info(f"Total findings: {len(findings)}")
    
    # Create advisor
    advisor = SecurityAdvisor()
    
    # Analyze
    assessment = advisor.analyze_findings(findings)
    logger.info(f"Risk Assessment: {assessment.risk_level}")
    
    # Generate outputs
    if args.gate in ["gate1", "gate2"]:
        # PR comment mode
        if args.output_comment:
            comment = advisor.generate_pr_comment(
                assessment,
                f"Gate {args.gate[-1]}"
            )
            
            with open(args.output_comment, "w") as f:
                f.write(comment)
            
            logger.info(f"PR comment written to {args.output_comment}")
            print(comment)
    
    if args.gate == "gate2":
        # Workflow summary mode
        if args.output_summary:
            summary = {
                "risk_level": assessment.risk_level,
                "summary": assessment.summary,
                "recommended_action": assessment.recommended_action,
                "findings_count": len(findings)
            }
            
            with open(args.output_summary, "w") as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Workflow summary written to {args.output_summary}")
    
    if args.gate == "gate3":
        # Deployment context mode
        if args.output_summary:
            context = advisor.generate_deployment_context(findings)
            
            with open(args.output_summary, "w") as f:
                f.write(context)
            
            logger.info(f"Deployment context written to {args.output_summary}")
            print(context)
    
    # Set GitHub output for PR comments
    if args.output_comment and args.pr_number:
        with open(args.output_comment) as f:
            comment_text = f.read()
        
        # Escape for GitHub output
        comment_escaped = comment_text.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
        print(f"::set-output name=pr-comment::{comment_escaped}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
