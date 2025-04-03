from django.db import models


class DataModel(models.Model):
    name = models.CharField(max_length=255)  # Пример поля


class Patient(models.Model):
    GENDER_CHOICES = [
        ('male', 'Мужчина'),
        ('female', 'Женщина'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=255, verbose_name="Имя")
    age = models.PositiveIntegerField(verbose_name="Возраст")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Пол")
    doctor_name = models.TextField(verbose_name="Имя врача")
    doctor_diagnosis = models.TextField(verbose_name="Диагноз врача")
    neural_diagnosis = models.TextField(verbose_name="Диагноз нейросети")
    server_path = models.TextField(verbose_name="Путь к данным")

    def __str__(self):
        return f"{self.name} ({self.age} лет)"

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"