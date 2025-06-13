import os
import logging

import torch
from fastapi import FastAPI, HTTPException, Query

from yolo_train_compare import InferencePipeline 


app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Убедитесь, что этот путь существует и доступен
BEST_MODEL_PATH = "yolo/best_model.txt" 
MEDIA_ROOT = "./media/png"


@app.get("/")
async def root():
    """
    Корневой эндпоинт для проверки состояния сервера.

    Returns:
        dict: Статус сервера.
    """

    return {"status": "YOLO inference server is up and running!"}


@app.post("/inference/")
async def run_inference(
    folder_id: str = Query(..., description="ID папки (например, '007')"),
    device: str = Query("cpu", description="Устройство для инференса: 'cpu' или 'cuda'")
):
    """
    Эндпоинт для запуска инференса YOLO на заданной папке с изображениями.

    Args:
        folder_id (str): ID папки с изображениями.
        device (str): Устройство для инференса ('cpu' или 'cuda').

    Returns:
        dict: Статус инференса.
    """

    logger.info(f"Запрос инференса для папки {folder_id} на {device}")

    if not os.path.exists(BEST_MODEL_PATH):
        raise HTTPException(status_code=500, detail="best_model.txt не найден. Сначала обучите модель.")

    with open(BEST_MODEL_PATH, "r") as f:
        best_model = f.read().strip()

    # Проверка, что best_model содержит путь и файл существует
    if not best_model or not os.path.exists(best_model):
        raise HTTPException(status_code=500, detail=f"Файл лучшей модели '{best_model}' не найден или best_model.txt пуст. Проверьте путь и существование файла.")

    try:
        # Вызываем статический метод с корректными параметрами
        InferencePipeline.run_inference(
            best_model=best_model,
            media_root=MEDIA_ROOT,
            single_folder_id=folder_id,
            device=device 
        )
        return {"status": "ok", "folder_id": folder_id, "device": device}
    except Exception as e:
        logger.error(f"Ошибка инференса: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))