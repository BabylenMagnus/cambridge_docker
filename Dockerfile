FROM python:3.9

WORKDIR /app

COPY . /app

RUN python3 -m pip install scipy gunicorn uvicorn fastapi beautifulsoup4 requests

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "1", "--timeout", "0", "-k", "uvicorn.workers.UvicornWorker", "app.webservice:app"]
