from django.shortcuts import redirect
from django.utils.decorators import sync_and_async_middleware
from django.http import FileResponse, Http404
from django.utils.deprecation import MiddlewareMixin

import os
from django.conf import settings


@sync_and_async_middleware
def redirect_if_not_authenticated_middleware(get_response):
    allowed_paths = ['/', '/login/', '/signup/']

    async def middleware_async(request):
        if (not request.user.is_authenticated and
                request.path not in allowed_paths):
            return redirect('/')
        response = await get_response(request)
        return response

    def middleware_sync(request):
        if (not request.user.is_authenticated and
                request.path not in allowed_paths):
            return redirect('/')
        response = get_response(request)
        return response

    return middleware_async if callable(get_response) and \
        hasattr(get_response, '__await__') else middleware_sync


class MediaFileMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith(settings.MEDIA_URL):
            file_path = request.path[len(settings.MEDIA_URL):].lstrip('/')
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            if os.path.exists(full_path) and os.path.isfile(full_path):
                return FileResponse(open(full_path, 'rb'))
            else:
                raise Http404(f"Медиафайл {file_path} не найден")