FROM python:3.12-slim

WORKDIR /api

RUN useradd -m apiuser

COPY requirements.txt .

RUN apt-get update && \
    apt-get upgrade --no-install-recommends -y && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

RUN chown -R apiuser:apiuser .

USER apiuser

# Copy python code late to make use of Dockers layer caching
COPY python/ .

EXPOSE 8080

ENTRYPOINT ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]