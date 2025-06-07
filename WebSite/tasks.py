import logging
import os

from celery import shared_task
from django.conf import settings

from .models import Patient
from .utils import convert_nii_to_png


logger = logging.getLogger(__name__)


def get_patient(patient_id):
    return Patient.objects.get(id=patient_id)


def update_patient_server_path(patient, server_path):
    patient.server_path = server_path
    patient.save()


@shared_task(bind=True)
def convert_patient_nii(self, patient_id, full_path, filename):
    logger.info(f"Start converting patient {patient_id}, file: {full_path}")
    try:
        # Формируем абсолютный путь к файлу
        nii_path = os.path.join(settings.MEDIA_ROOT, full_path)

        patient = get_patient(patient_id)

        output_folder = os.path.join("png", str(patient.id))
        server_path = str(patient.id)

        logger.info(f"Путь к nii файлу: {nii_path}")
        logger.info(f"Папка вывода: {output_folder}")

        convert_nii_to_png(nii_path, output_folder, filename, slice_range=(124, 180))

        update_patient_server_path(patient, server_path)

        logger.info(f"Successfully converted patient {patient_id} file {filename}")
    except Exception as e:
        logger.error(f"Error converting patient {patient_id}: {e}", exc_info=True)
        raise
