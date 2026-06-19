# Retraining worker. CPU torch; run on demand (scheduler.py --once) or as a
# long-lived weekly scheduler. Mounts the deploy dir so a promoted model lands
# where the inference server reads it.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
        torch==2.5.1 torchvision==0.20.1 \
    && pip install -r requirements.txt
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

COPY . .
CMD ["python", "scheduler.py", "--once"]
