import logging
import os
import requests

from celery import shared_task
from django.conf import settings

from .utils import convert_nii_to_png, get_patient, update_patient_server_path


logger = logging.getLogger(__name__)


# URL сервера YOLO, который можно переопределить через переменную окружения
YOLO_SERVER_URL = os.getenv("YOLO_SERVER_URL",
                            "http://yoloserver:8001/inference/")


@shared_task(bind=True)
def convert_patient_nii(self, patient_id, full_path, filename):
    """
    Асинхронная задача для конвертации NIfTI файла в PNG и отправки на обработку YOLO-серверу.

    Args:
        self (Celery task instance): Экземпляр задачи Celery.
        patient_id (int): Уникальный идентификатор пациента.
        full_path (str): Полный путь к NIfTI файлу.
        filename (str): Имя файла.
    """

    logger.info(f"Start converting patient {patient_id}, file: {full_path}")
    try:
        # Абсолютный путь к .nii
        nii_path = os.path.join(settings.MEDIA_ROOT, full_path)

        # Получаем пациента
        patient = get_patient(patient_id)

        # Новый путь: media/png/<ID>/raw/
        raw_folder_name = os.path.join(str(patient.id), "raw")
        output_folder = os.path.join("png", raw_folder_name)

        # Сохраняем "ID" как server_path
        server_path = str(patient.id)

        logger.info(f"Путь к nii файлу: {nii_path}")
        logger.info(f"Папка вывода: {output_folder}")

        # Конвертация
        convert_nii_to_png(nii_path, output_folder, filename, slice_range=(124, 180))

        # Обновляем путь пациента
        update_patient_server_path(patient, server_path)

        logger.info(f"Successfully converted patient {patient_id}, folder: {output_folder}")

        # Отправка запроса на YOLO-сервер для начала инференса
        logger.info(f"Sending inference request to YOLO server for folder: {server_path}")
        response = requests.post(YOLO_SERVER_URL, params={"folder_id": f"{server_path}"}, timeout=600)

        if response.status_code == 200:
            logger.info(f"YOLO inference started for folder {server_path}")
        else:
            logger.warning(f"YOLO server returned status {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"Error converting patient {patient_id}: {e}", exc_info=True)
        raise
