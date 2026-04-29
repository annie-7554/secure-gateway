#!/usr/bin/env bash
set -euo pipefail

echo "Running local security scans..."

if ! command -v semgrep >/dev/null 2>&1; then
  echo "semgrep not found, installing via pip"
  pip install --user semgrep
fi
semgrep --config .semgrep/rules.yml || true

if ! command -v trufflehog >/dev/null 2>&1; then
  echo "trufflehog not found, installing via pip"
  pip install --user trufflehog
fi
trufflehog git --json . > trufflehog.json || true

# Dependency-Check requires docker image; run if docker available
if command -v docker >/dev/null 2>&1; then
  mkdir -p dependency-check-scan
  docker run --rm -v "$(pwd):/src" -w /src owasp/dependency-check:latest --scan . --format SARIF --out /src/dependency-check-scan || true
  echo "Dependency-Check SARIF may be in dependency-check-scan/"
fi

echo "Scans completed."
