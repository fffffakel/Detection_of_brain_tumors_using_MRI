from django.contrib import admin
from .models import Patient  # Импортируй модель пациентов

    
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "age", "gender", "doctor_name", "doctor_diagnosis", "neural_diagnosis")
    search_fields = ("name", "doctor_name", "neural_diagnosis")
    list_filter = ("gender", "doctor_name")