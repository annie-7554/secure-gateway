# Secure Gateway

[![PR Security Gate](https://github.com/annie-7554/secure-gateway/actions/workflows/pr-security.yml/badge.svg)](https://github.com/annie-7554/secure-gateway/actions/workflows/pr-security.yml) [![Build Security Gate](https://github.com/annie-7554/secure-gateway/actions/workflows/build-security.yml/badge.svg)](https://github.com/annie-7554/secure-gateway/actions/workflows/build-security.yml)

DevSecOps CI/CD Pipeline with Three Security Gates

This repository demonstrates a production-like DevSecOps pipeline using only free and open-source tools. It contains a Flask web application, GitHub Actions workflows for PR/build/deploy security gates, Kubernetes manifests, Kyverno policies, and documentation.

Important quick links:
- Docs: docs/
- Examples for demos: examples/

Setup notes:
- See docs/secrets.md for required GitHub secrets (COSIGN_PRIVATE_KEY, COSIGN_PASSWORD, GHCR_TOKEN, KUBECONFIG)
- For production deployments, enable a GitHub Environment named `production` and require reviewers (docs/environment-protection.md)

