from django.shortcuts import redirect
from django.utils.decorators import sync_and_async_middleware


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
