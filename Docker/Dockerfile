FROM python:3.13-slim-trixie

LABEL maintainer="ma-tecik"
LABEL org.opencontainers.image.authors="ma-tecik"

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

VOLUME ["/app/data"]
EXPOSE 20340
ENTRYPOINT ["gunicorn", "-b 0.0.0.0:20340", "app:app"]