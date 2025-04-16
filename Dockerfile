# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./scr ./scr

CMD ["uvicorn", "scr.main:app", "--host", "0.0.0.0", "--port", "8080"]
