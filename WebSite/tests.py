from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Patient
from .tasks import convert_patient_nii

# from .forms import PatientForm  # Раскомментируй, если используешь форму


class PatientModelTest(TestCase):
    def test_str_representation(self):
        patient = Patient(name="Иван Иванов", age=30)
        self.assertEqual(str(patient), "Иван Иванов (30 лет)")


class PatientViewsTest(TestCase):
    def setUp(self):
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
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 302)  # redirect to /

    def test_patients_view_logged_in(self):
        self.client.login(username='doc', password='pass')
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пациент')


class CeleryTaskTest(TestCase):
    def setUp(self):
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
        with self.assertRaises(Exception):
            convert_patient_nii(
                self.patient.id, 'non_existing_path.nii', 'file.nii'
            )


class MiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_redirect_if_not_authenticated(self):
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)


# Раскомментируй, если используешь PatientForm
# class PatientFormTest(TestCase):
#     def test_valid_form(self):
#         data = {
#             'name': 'Андрей',
#             'age': 25,
#             'gender': 'male',
#             'doctor_name': 'Доктор Хаус',
#             'doctor_diagnosis': 'Здоров',
#             'neural_diagnosis': 'OK',
#             'server_path': '2'
#         }
#         form = PatientForm(data=data)
#         self.assertTrue(form.is_valid())
