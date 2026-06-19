# VisionGuard inference server. Torch CPU wheels keep the image runnable without
# a GPU; the trained model (models/best.pt) is mounted in via docker-compose.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# OpenCV runtime libs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
        torch==2.5.1 torchvision==0.20.1 \
    && pip install -r requirements.txt

# Pre-fetch the fallback model so the server boots offline even with no trained model.
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

COPY . .
EXPOSE 8001
CMD ["uvicorn", "inference:app", "--host", "0.0.0.0", "--port", "8001"]
