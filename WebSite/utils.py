import os
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Установка backend ДО pyplot
import matplotlib.pyplot as plt
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def convert_nii_to_png(input_path, output_base_folder, filename, slice_range=(124, 180)):
    logger.info(f"Начинаем конвертацию {input_path}")
    try:
        if not os.path.exists(input_path):
            logger.error(f"Файл не найден: {input_path}")
            raise FileNotFoundError(f"Нет такого файла: {input_path}")

        nifti_image = nib.load(input_path)
        image_data = nifti_image.get_fdata()
        _, _, z_dim = image_data.shape

        basename = filename.replace(".nii.gz", "").replace(".nii", "")
        abs_output_folder = os.path.join(settings.MEDIA_ROOT, output_base_folder, basename)
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
