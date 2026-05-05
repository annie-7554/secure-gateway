#!/bin/bash
# Local setup script - run security tools without CI/CD

set -e  # Exit on error

echo "=== DevSecOps Pipeline - Local Setup ==="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }

echo "✓ Prerequisites installed"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Install Semgrep (SAST)
echo "Checking Semgrep..."
if ! command -v semgrep >/dev/null 2>&1; then
    echo "  Installing semgrep..."
    pip install semgrep
fi
echo "✓ Semgrep ready"
echo ""

# Install Trivy (Container scanning)
echo "Checking Trivy..."
if ! command -v trivy >/dev/null 2>&1; then
    echo "  Installing trivy..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install trivy
    else
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    fi
fi
echo "✓ Trivy ready"
echo ""

# Try to install TruffleHog (optional)
echo "Checking TruffleHog..."
if ! command -v trufflehog >/dev/null 2>&1; then
    echo "  Note: TruffleHog not installed (optional, requires GitHub Actions for PR scanning)"
fi
echo ""

# Build Docker image
echo "Building Docker image..."
docker build -t devsecops-app:local -f docker/Dockerfile .
echo "✓ Docker image built"
echo ""

# Run Semgrep locally
echo "Running Semgrep SAST scan..."
semgrep --config=p/owasp-top-ten --config=p/cwe-top-25 src/ || echo "  (Review findings above)"
echo "✓ Semgrep scan complete"
echo ""

# Run Trivy on image
echo "Running Trivy container scan..."
trivy image devsecops-app:local --severity HIGH,CRITICAL || echo "  (Review findings above)"
echo "✓ Trivy scan complete"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review findings from Semgrep and Trivy above"
echo "2. Test the Flask app: python src/app.py"
echo "3. Run the full pipeline in GitHub Actions by opening a PR"
echo "4. Read docs/SECURITY.md for how each gate works"
echo ""
