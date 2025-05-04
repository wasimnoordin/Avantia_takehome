# Dockerfile

FROM python:3.11-slim
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest.py app.py ./


EXPOSE 5000

CMD ["sh", "-c", "python ingest.py && python app.py"]
