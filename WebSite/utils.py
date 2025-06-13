import os
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from django.conf import settings

from .models import Patient


logger = logging.getLogger(__name__)


def convert_nii_to_png(input_path, output_base_folder, filename, slice_range=(124, 180)):
    """
    Конвертирует NIfTI файл в серию изображений PNG.

    Args:
        input_path (str): Путь к входному NIfTI файлу.
        output_base_folder (str): Базовая папка для сохранения изображений PNG.
        filename (str): Имя файла (не используется в текущей реализации).
        slice_range (tuple): Диапазон срезов для конвертации (по умолчанию от 124 до 180).
    """

    logger.info(f"Начинаем конвертацию {input_path}")
    try:
        if not os.path.exists(input_path):
            logger.error(f"Файл не найден: {input_path}")
            raise FileNotFoundError(f"Нет такого файла: {input_path}")

        nifti_image = nib.load(input_path)
        image_data = nifti_image.get_fdata()
        _, _, z_dim = image_data.shape

        abs_output_folder = os.path.join(settings.MEDIA_ROOT, output_base_folder)
        os.makedirs(abs_output_folder, exist_ok=True)
        logger.info(f"Папка для PNG: {abs_output_folder}")

        start_slice, end_slice = slice_range
        for slice_number in range(start_slice, end_slice + 1):
            if slice_number >= z_dim:
                logger.warning(f"Slice {slice_number} превышает размерность {z_dim}")
                continue

            slice_data = image_data[:, :, slice_number]
            min_val, max_val = np.min(slice_data), np.max(slice_data)
            if max_val != min_val:
                slice_data_normalized = (slice_data - min_val) / (max_val - min_val)
            else:
                slice_data_normalized = np.zeros_like(slice_data)

            plt.figure(figsize=(6, 6))
            plt.imshow(slice_data_normalized, cmap="gray", origin="lower")
            plt.axis("off")

            output_file = os.path.join(abs_output_folder, f"{slice_number}.png")
            plt.savefig(output_file, bbox_inches="tight", pad_inches=0, dpi=300)
            plt.close()
            logger.info(f"Сохранён срез: {output_file}")

        logger.info("Конвертация завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка конвертации nii в png: {e}", exc_info=True)
        raise


def get_patient(patient_id):
    """
    Получает объект пациента по его ID.

    Args:
        patient_id (int): Уникальный идентификатор пациента.

    Returns:
        Patient: Объект пациента.
    """

    return Patient.objects.get(id=patient_id)


def update_patient_server_path(patient, server_path):
    """
    Обновляет путь сервера для указанного пациента.

    Args:
        patient (Patient): Объект пациента.
        server_path (str): Новый путь сервера для пациента.
    """

    patient.server_path = server_path
    patient.save()
