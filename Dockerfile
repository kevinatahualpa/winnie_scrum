FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY . .

RUN mkdir -p /app/logs /app/staticfiles && \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 config.wsgi:application"]
