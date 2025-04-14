from django.shortcuts import redirect


class RedirectIfNotAuthenticatedMiddleware:
    """
    Middleware для проверки, аутентифицирован ли пользователь.
    Если нет - перенаправляем его на главную страницу.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Если пользователь не аутентифицирован и не на главной странице
        if not request.user.is_authenticated and request.path != '/':
            return redirect('/')
        
        response = self.get_response(request)
        return response
