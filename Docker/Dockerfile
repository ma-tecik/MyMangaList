FROM python:3.13-slim-trixie

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y sqlite3 cron && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

COPY Docker/backup.sh /backup.sh
COPY Docker/app.sh /app.sh
COPY Docker/cronjob /etc/cron.d/mml-cron

RUN chmod 0644 /etc/cron.d/mml-cron && \
    chmod +x /backup.sh /app.sh

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

EXPOSE 20340
ENTRYPOINT ["/app.sh"]