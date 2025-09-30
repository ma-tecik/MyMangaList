FROM python:3.13-slim-trixie

LABEL maintainer="ma-tecik"
LABEL org.opencontainers.image.authors="ma-tecik"

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y sqlite3 cron && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

RUN mv Docker/backup.sh /backup.sh && \
    mv Docker/app.sh /app.sh && \
    rmdir Docker && \
    chmod +x /backup.sh /app.sh

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

EXPOSE 20340
ENTRYPOINT ["/app.sh"]