"""Prompt templates for security advisory analysis.

Focus on risk assessment guidance (low/moderate/high risk) and
developer-friendly remediation suggestions.
"""


RISK_ASSESSMENT_SYSTEM_PROMPT = """You are a security advisor analyzing vulnerability findings.

Your goal is to help developers understand risks and fix issues.

For each finding, provide:
1. Risk Assessment: low risk, moderate risk, or high risk
2. Clear explanation of why (in 1-2 sentences)
3. Practical remediation steps (numbered)
4. Expected outcome after remediation

Keep explanations technical but accessible to developers.
Use JSON format for structured output."""


RISK_ASSESSMENT_PROMPT = """Analyze these security findings and provide risk assessment and guidance:

{findings_text}

For each finding:
1. Assess risk level: low risk, moderate risk, or high risk
2. Explain why (impact + exploitability)
3. Give practical fix steps
4. Estimate remediation time

Return JSON with this structure:
{{
  "findings": [
    {{
      "title": "Finding title",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "risk_level": "low risk|moderate risk|high risk",
      "explanation": "Why this is a risk...",
      "remediation_steps": ["Step 1", "Step 2", ...],
      "time_estimate": "5 min|30 min|1 hour"
    }}
  ],
  "summary": "Brief overall assessment...",
  "recommended_action": "fix immediately|fix in next sprint|monitor"
}}"""


REMEDIATION_PROMPT = """Given this vulnerability, provide step-by-step remediation:

Vulnerability: {vuln_title}
Severity: {severity}
Description: {description}

Provide:
1. Root cause explanation
2. Specific fix steps (code snippets if applicable)
3. Testing recommendations
4. Prevention tips for future

Format as numbered steps that a developer can follow."""


DEPLOYMENT_CONTEXT_PROMPT = """Assess the security context for this deployment.

Build findings:
{findings_summary}

Provide:
1. Overall risk assessment (low/moderate/high)
2. Critical blockers (if any)
3. Items to monitor in production
4. Rollback trigger points

Keep it concise (deployment decision context, not blocking decision)."""


def format_risk_assessment_prompt(findings_text: str) -> str:
    """Format risk assessment prompt with findings."""
    return RISK_ASSESSMENT_PROMPT.format(findings_text=findings_text)


def format_remediation_prompt(title: str, severity: str, description: str) -> str:
    """Format remediation guidance prompt."""
    return REMEDIATION_PROMPT.format(
        vuln_title=title,
        severity=severity,
        description=description
    )


def format_deployment_context_prompt(findings_summary: str) -> str:
    """Format deployment context assessment prompt."""
    return DEPLOYMENT_CONTEXT_PROMPT.format(findings_summary=findings_summary)
