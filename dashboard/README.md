# Security Advisor Dashboard

A modern React dashboard for monitoring AI-assisted security findings in the DevSecOps pipeline.

## Features

- **Dashboard Overview**: High-level statistics on security posture
- **Security Gates**: Detailed view of Gate 1, Gate 2, and Gate 3 status
- **Recent PRs**: Track recent pull requests and their security assessments
- **Real-time Status**: Monitor findings and risk levels
- **AI Advisory Context**: View sample security advisory comments

## Local Development

### Prerequisites

- Node.js 18+
- npm

### Installation

```bash
cd dashboard
npm install
```

### Running Locally

```bash
npm run dev
```

This will start the dev server on `http://localhost:3000` and open it in your browser.

### Building for Production

```bash
npm run build
```

The built assets will be in the `dist/` directory.

## Dashboard Sections

### Overview Tab
- Total PRs scanned
- Current risk level assessment
- Critical findings count
- Severity breakdown (High/Medium/Low)
- Security gates status

### Security Gates Tab
- Detailed view of each gate:
  - Gate 1: Code Security (Semgrep, TruffleHog, Snyk)
  - Gate 2: Build Security (Trivy, SBOM)
  - Gate 3: Deployment (Approval, RBAC, Kyverno)
- Last check timestamp
- Findings and risk levels
- Recommended actions

### Recent PRs Tab
- Recent pull request assessments
- PR author and status
- Security findings summary
- Risk level indicators
- Sample advisory comments

## Deployment

The dashboard is automatically deployed to GitHub Pages when changes are pushed to the `main` branch (triggered by changes in the `dashboard/` directory).

GitHub Pages URL: `https://<username>.github.io/secure-gateway/`

## Integration with AI Security Advisor

The dashboard can be extended to pull real data from:
- GitHub Actions artifacts (findings.json)
- Security advisor API endpoints
- GitHub GraphQL API for PR data

Currently uses mock data for demonstration.

## Technologies

- React 18
- Vite (build tool)
- CSS Grid/Flexbox
- Responsive design

## License

MIT
