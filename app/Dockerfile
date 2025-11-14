# Use an official Python runtime as a parent image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (add locale/timezone tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# copy only requirements first for better layer caching
COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application
COPY . .

EXPOSE 8080

# Use shell form so $PORT can be expanded at runtime (default to 8080)
CMD ["sh", "-lc", "gunicorn app.server:app --bind 0.0.0.0:${PORT:-8080} --workers 1"]
