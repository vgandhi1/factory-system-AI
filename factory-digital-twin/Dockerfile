FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
# default: publish to NATS in real-time; override CMD for batch/file mode
CMD ["python", "run.py", "--realtime"]
