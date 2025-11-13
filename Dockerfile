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

EXPOSE 5000

# Replace 'src:app' if your app object lives elsewhere (e.g. 'app:app')
CMD ["gunicorn", "src:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
