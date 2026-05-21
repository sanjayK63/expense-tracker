FROM python:3.11-slim

# System deps required by weasyprint + pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects PORT; default to 8000 for local docker run
ENV PORT=8000

EXPOSE 8080

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
