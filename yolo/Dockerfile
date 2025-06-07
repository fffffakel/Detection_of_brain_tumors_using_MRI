FROM ultralytics/ultralytics:latest

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . .

# Установим FastAPI и Uvicorn
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn

EXPOSE 8001

CMD ["uvicorn", "yolo.server:app", "--host", "0.0.0.0", "--port", "8001"]
