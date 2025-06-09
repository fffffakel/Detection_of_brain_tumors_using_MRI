import os

import matplotlib
matplotlib.use('Agg')  # Используем без GUI
import matplotlib.pyplot as plt
import numpy as np

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.text import get_valid_filename

from .models import Patient
from .tasks import convert_patient_nii


# === User registration ===

def validate_registration(username, email, password, confirm_password):
    """
    Проверяет валидность данных регистрации.

    Args:
        username (str): Имя пользователя.
        email (str): Email пользователя.
        password (str): Пароль пользователя.
        confirm_password (str): Подтверждение пароля.

    Returns:
        str or None: Сообщение об ошибке или None, если данные валидны.
    """

    if password != confirm_password:
        return "Пароли не совпадают!"
    if User.objects.filter(username=username).exists():
        return "Имя пользователя уже занято!"
    if User.objects.filter(email=email).exists():
        return "Этот email уже зарегистрирован!"
    return None


def create_user_account(username, email, password):
    """
    Создает новый аккаунт пользователя.

    Args:
        username (str): Имя пользователя.
        email (str): Email пользователя.
        password (str): Пароль пользователя.

    Returns:
        User: Созданный объект пользователя.
    """

    user = User.objects.create_user(username=username,
                                    email=email,
                                    password=password)
    user.save()
    return user


def register_view(request):
    """
    Представление для регистрации нового пользователя.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с отображением страницы регистрации или перенаправлением на страницу входа.
    """

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        error = validate_registration(username,
                                      email,
                                      password,
                                      confirm_password)
        if error:
            messages.error(request, error)
            return render(request, "WebSite/signup.html")

        create_user_account(username, email, password)
        messages.success(request,
                         "Регистрация успешна! Теперь войдите в аккаунт.")
        return redirect("login")

    return render(request, "WebSite/signup.html")


# === User login/logout ===

def login_view(request):
    """
    Представление для входа пользователя в систему.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с отображением страницы входа или перенаправлением на домашнюю страницу.
    """

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,
                            username=username,
                            password=password)

        if user is not None:
            login(request, user)
            messages.success(request,
                             "Вы успешно вошли в систему!")
            return redirect("home")
        else:
            messages.error(request,
                           "Неверное имя пользователя или пароль!")

    return render(request, "WebSite/login.html")


def logout_view(request):
    """
    Представление для выхода пользователя из системы.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с перенаправлением на домашнюю страницу.
    """

    logout(request)
    messages.success(request,
                     "Вы вышли из системы.")
    return redirect("home")


# === Home page view ===

def home(request):
    """
    Представление для домашней страницы.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с отображением домашней страницы.
    """

    return render(request, 'WebSite/home.html')


# === Patients list view ===

@login_required
def patients(request):
    """
    Представление для отображения списка пациентов.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с отображением списка пациентов.
    """

    patients_data = (
        Patient.objects
        .filter(doctor_name=request.user.username)
        .order_by('id')
    )
    return render(request, 'WebSite/patients.html', {'patients': patients_data})


# === NII file handling service ===

class NiiFileHandler:
    """
    Класс для обработки NIfTI файлов.
    """

    ALLOWED_EXTENSIONS = {".nii", ".nii.gz"}

    @staticmethod
    def is_valid_extension(filename):
        """
        Проверяет, имеет ли файл допустимое расширение.

        Args:
            filename (str): Имя файла.

        Returns:
            bool: True, если расширение допустимо, иначе False.
        """

        ext = os.path.splitext(filename)[-1].lower()
        if filename.endswith(".nii.gz"):
            ext = ".nii.gz"
        return ext in NiiFileHandler.ALLOWED_EXTENSIONS

    @staticmethod
    def save_file(user, file):
        """
        Сохраняет загруженный NIfTI файл.

        Args:
            user (User): Объект пользователя.
            file (UploadedFile): Загруженный файл.

        Returns:
            tuple: Кортеж с именем файла и полным путем к файлу.
        """

        filename = get_valid_filename(file.name)
        if not NiiFileHandler.is_valid_extension(filename):
            raise SuspiciousOperation(f"Invalid file type: {filename}")

        user_folder = os.path.join("nii", user.username)
        file_path = os.path.join(user_folder, filename)
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        full_path = default_storage.path(saved_path)
        return filename, full_path


def create_patient_record(data, doctor_name):
    """
    Создает новую запись пациента в базе данных.

    Args:
        data (dict): Словарь с данными пациента.
        doctor_name (str): Имя врача, создающего запись.

    Returns:
        Patient: Созданный объект пациента.
    """

    return Patient.objects.create(
        name=data['name'],
        age=int(data['age']),
        gender=data['gender'],
        doctor_name=doctor_name,
        doctor_diagnosis=data['doctor_diagnosis'],
        neural_diagnosis="—"
    )


@login_required
def convert(request):
    """
    Представление для загрузки NIfTI файла и создания записи пациента.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ HTTP с отображением страницы загрузки файла или перенаправлением на ту же страницу.
    """

    if request.method == "POST" and request.FILES.get("nii_file"):
        nii_file = request.FILES["nii_file"]

        patient_data = {
            'name': request.POST.get("name"),
            'age': request.POST.get("age"),
            'gender': request.POST.get("gender"),
            'doctor_diagnosis': request.POST.get("doctor_diagnosis"),
        }
        doctor_name = request.user.username

        filename, full_path = NiiFileHandler.save_file(request.user, nii_file)
        patient = create_patient_record(patient_data, doctor_name)
        convert_patient_nii.delay(patient.id, full_path, filename)

        return redirect("convert")

    return render(request, "WebSite/convert.html")


# === View PNG images and folders ===

@login_required
def view_pngs(request, folder):
    """
    Представление для просмотра PNG изображений и подпапок.

    Args:
        request (HttpRequest): Объект запроса.
        folder (str): Путь к папке с изображениями.

    Returns:
        HttpResponse: Ответ HTTP с отображением списка изображений или подпапок.
    """

    base_folder = os.path.join(settings.MEDIA_ROOT, "png", folder)

    if not os.path.exists(base_folder):
        raise Http404("Папка не найдена")

    dirs, files = default_storage.listdir(base_folder)

    if dirs:
        subfolder_urls = [os.path.join(folder, d) for d in sorted(dirs)]
        context = {
            'folder': folder,
            'subfolders': zip(subfolder_urls, sorted(dirs)),
        }
        return render(request, 'WebSite/folder_list.html', context)

    png_files = sorted([f for f in files if f.lower().endswith('.png')])
    png_file_urls = [
        os.path.join(settings.MEDIA_URL, 'png', folder, f)
        for f in png_files
    ]
    page = request.GET.get('page', 1)
    paginator = Paginator(list(zip(png_file_urls, png_files)), 20)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'folder': folder,
        'png_files': page_obj.object_list,
        'media_url': settings.MEDIA_URL,
        'page_obj': page_obj,
    }
    return render(request, 'WebSite/view_pngs.html', context)
