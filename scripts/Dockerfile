FROM python:3.11-slim
RUN apt update && apt install -y exiftool
WORKDIR /app
COPY indexer.py .
RUN pip install watchdog requests
CMD ["python", "indexer.py"]