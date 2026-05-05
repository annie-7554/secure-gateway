# Security-first Dockerfile - demonstrates hardening principles
# Base: Python 3.11-slim (smaller attack surface than full image)
FROM python:3.11-slim

# Metadata: helps with scanning and tracking
LABEL maintainer="devsecops@example.com" \
      version="1.0" \
      description="Entry-level DevSecOps demo application"

# SECURITY: Set non-root user BEFORE installing anything
# Why: Container escapes run as the user inside container
#      If container is compromised, attacker has minimal privileges
RUN groupadd -r appuser && useradd -r -g appuser appuser

# SECURITY: Install only necessary packages, clean cache
# Why: Reduces CVE surface area + image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching optimization)
COPY requirements.txt .

# SECURITY: Install Python dependencies in isolated environment
# Why: Prevents dependency conflicts, easier to track
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# SECURITY: Change ownership to non-root user
# Why: Prevents container from writing to app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user - all processes run as unprivileged user
USER appuser

# SECURITY: Expose only necessary port (not privileged port < 1024)
# Why: Limits what container can do even if compromised
EXPOSE 8000

# SECURITY: Add healthcheck for orchestration
# Why: Kubernetes/Docker can auto-restart unhealthy containers
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# SECURITY: Use exec form of ENTRYPOINT (prevents shell injection)
# Why: Direct process execution without intermediate shell
ENTRYPOINT ["python", "-u", "app.py"]
