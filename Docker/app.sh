#!/bin/bash
cron
exec gunicorn -b 0.0.0.0:20340 app:app