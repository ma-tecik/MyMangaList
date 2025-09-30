#!/bin/bash
echo "Starting app..."
cron
echo "0 1 * * * /backup.sh >> /app/data/logs/cron.log 2>&1" | crontab -
exec gunicorn -b 0.0.0.0:20340 app:app