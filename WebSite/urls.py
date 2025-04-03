from django.urls import path
from . import views  # Импортируем представления из вашего приложения
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('model/', views.model, name='model'),
    path('predictions/', views.predictions, name='predictions'),
    path('convert/', views.convert, name='convert'),
    path('patients/', views.patients, name='patients'),
    path('download/<str:filename>/', views.download, name='download'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
