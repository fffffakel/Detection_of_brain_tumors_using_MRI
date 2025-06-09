import os

from django.shortcuts import redirect
from django.http import FileResponse, Http404
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


def redirect_if_not_authenticated_middleware(get_response):
    """
    Middleware для перенаправления неавторизованных пользователей на главную страницу.

    Args:
        get_response: Следующий middleware или обработчик запроса в цепочке.

    Returns:
        HttpResponse: Ответ HTTP
    """

    allowed_paths = ['/', '/login/', '/signup/']

    def middleware_sync(request):
        if (not request.user.is_authenticated and
                request.path not in allowed_paths):
            return redirect('/')
        response = get_response(request)
        return response

    return middleware_sync


class MediaFileMiddleware(MiddlewareMixin):
    """
    Middleware для обслуживания медиафайлов.
    """
    def process_request(self, request):
        """
        Обрабатывает запросы к медиафайлам.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            FileResponse: Ответ с медиафайлом, если файл существует.
            Http404: Исключение 404, если файл не найден.
        """
        if request.path.startswith(settings.MEDIA_URL):
            file_path = request.path[len(settings.MEDIA_URL):].lstrip('/')
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            if os.path.exists(full_path) and os.path.isfile(full_path):
                return FileResponse(open(full_path, 'rb'))
            else:
                raise Http404(f"Медиафайл {file_path} не найден")