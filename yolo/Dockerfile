# Используем готовый CPU-образ от Ultralytics
FROM ultralytics/ultralytics:latest-cpu

# Рабочая директория
WORKDIR /workspace

# Копируем зависимости (если нужно что-то докачать)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Открываем порт для FastAPI
EXPOSE 8001

# Запуск сервера
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]