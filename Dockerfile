FROM python:3.11-slim

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

USER appuser
CMD ["gunicorn", "app.app:app", "-b", "0.0.0.0:8000"]
