FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN mkdir -p output data \
    && [ -f data/master_profile.json ] || cp data/demo_profile.json data/master_profile.json

ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# PORT is set by hosts like Render; generation takes 20-60s, so allow a long timeout
CMD ["sh", "-c", "gunicorn --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:${PORT:-5000} app:app"]
