from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Patient
from .tasks import convert_patient_nii


class PatientModelTest(TestCase):
    """
    Тесты для модели Patient.
    """

    def test_str_representation(self):
        """
        Проверяет строковое представление объекта Patient.
        """
        patient = Patient(name="Иван Иванов", age=30)
        self.assertEqual(str(patient), "Иван Иванов (30 лет)")


class PatientViewsTest(TestCase):
    """
    Тесты для представлений (views) приложения.
    """

    def setUp(self):
        """
        Настройка тестового клиента и создания пользователя и пациента.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='doc', password='pass')
        self.patient = Patient.objects.create(
            name='Пациент',
            age=40,
            gender='male',
            doctor_name='doc',
            doctor_diagnosis='ОК',
            neural_diagnosis='ОК',
            server_path='1'
        )

    def test_patients_view_redirects_if_not_logged_in(self):
        """
        Проверяет, что представление /patients/ перенаправляет неавторизованного пользователя на главную страницу.
        """
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 302)  # redirect to /

    def test_patients_view_logged_in(self):
        """
        Проверяет, что представление /patients/ доступно для авторизованного пользователя и содержит имя пациента.
        """
        self.client.login(username='doc', password='pass')
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пациент')


class CeleryTaskTest(TestCase):
    """
    Тесты для задач Celery.
    """

    def setUp(self):
        """
        Создание пациента для использования в тестах задач Celery.
        """
        self.patient = Patient.objects.create(
            name='Тест',
            age=20,
            gender='male',
            doctor_name='doc',
            doctor_diagnosis='',
            neural_diagnosis='',
            server_path=''
        )

    def test_convert_task_raises_on_missing_file(self):
        """
        Проверяет, что задача convert_patient_nii выбрасывает исключение при отсутствии файла.
        """
        with self.assertRaises(Exception):
            convert_patient_nii(
                self.patient.id, 'non_existing_path.nii', 'file.nii'
            )


class MiddlewareTest(TestCase):
    """
    Тесты для мидлвари.
    """

    def setUp(self):
        """
        Настройка тестового клиента.
        """
        self.client = Client()

    def test_redirect_if_not_authenticated(self):
        """
        Проверяет, что мидлварь перенаправляет неавторизованного пользователя на главную страницу.
        """
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)
