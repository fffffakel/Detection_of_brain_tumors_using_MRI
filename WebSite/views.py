import os
import subprocess

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import FileResponse
from django.core.paginator import Paginator



from .models import DataModel, Patient


ALLOWED_EXTENSIONS = {".nii", ".nii.gz"}  # Разрешенные расширения


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            messages.error(request, "Пароли не совпадают!")
            return render(request, "WebSite/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Имя пользователя уже занято!")
            return render(request, "WebSite/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Этот email уже зарегистрирован!")
            return render(request, "WebSite/signup.html")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, "Регистрация успешна! Теперь войдите в аккаунт.")
        return redirect("login")

    return render(request, "WebSite/signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему!")
            return redirect("home")  # Перенаправляем на главную страницу
        else:
            messages.error(request, "Неверное имя пользователя или пароль!")
    
    return render(request, "WebSite/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Вы вышли из системы.")
    return redirect("home")


def home_view(request):
    data = DataModel.objects.all() if request.user.is_authenticated else None
    return render(request, 'WebSite/home.html', {'data': data})


def home(request):
    return render(request, 'WebSite/home.html')


def model(request):
    return render(request, 'WebSite/model.html')


def predictions(request):
    return render(request, 'WebSite/predictions.html')


# def convert(request):
#     return render(request, 'WebSite/convert.html')


def patients(request):
    patients_data = Patient.objects.all()  # Получаем всех пациентов
    return render(request, 'WebSite/patients.html', {'patients': patients_data})


@login_required
def convert(request):
    user_folder = os.path.join("nii", request.user.username)  # Используем относительный путь

    if request.method == "POST" and request.FILES.get("nii_file"):
        nii_file = request.FILES["nii_file"]

        # Проверяем имя файла
        filename = nii_file.name
        if ".." in filename or filename.startswith("/"):
            raise SuspiciousOperation("Detected path traversal attempt in file name.")

        # Проверка расширения файла
        ext = os.path.splitext(filename)[-1].lower()
        if filename.endswith(".nii.gz"):  # Обрабатываем двойное расширение
            ext = ".nii.gz"

        if ext not in ALLOWED_EXTENSIONS:
            raise SuspiciousOperation(f"Invalid file type: {ext}")

        # Формируем безопасный путь
        file_path = os.path.join(user_folder, filename)

        # Сохраняем файл через default_storage
        file_path = default_storage.save(file_path, ContentFile(nii_file.read()))

    # Получаем список файлов
    if default_storage.exists(user_folder):
        files = default_storage.listdir(user_folder)[1]
    else:
        files = []

    # Пагинация
    paginator = Paginator(files, 5)  # 15 файлов на страницу
    page_num = request.GET.get('page', 1)  # Получаем номер страницы из параметров запроса
    page = paginator.get_page(page_num)  # Получаем страницу

    return render(request, "WebSite/convert.html", {
        "files": page,  # Передаем объект страницы
        "page_num": page.number,  # Текущий номер страницы
        "total_pages": paginator.num_pages,  # Общее количество страниц
        "media_url": settings.MEDIA_URL
    })
    
    
@login_required
def download(request, filename):
    user_folder = os.path.join("nii", request.user.username)
    file_path = os.path.join(user_folder, filename)

    # Проверяем, существует ли файл
    if not default_storage.exists(file_path):
        raise SuspiciousOperation("File does not exist.")

    # Отдаем файл через FileResponse без изменения размера
    return FileResponse(default_storage.open(file_path, 'rb'), content_type='application/octet-stream')