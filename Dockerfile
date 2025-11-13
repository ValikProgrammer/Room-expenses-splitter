# Use an official Python runtime as a parent image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (if any) and pip requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || \
    (pip install --no-cache-dir flask gunicorn && true)

# Copy application source
COPY . .

EXPOSE 5000

# Use gunicorn to serve the Flask app defined in src/__init__.py as "app"
CMD ["gunicorn", "src:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
