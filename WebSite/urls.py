from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('convert/', views.convert, name='convert'),
    path('patients/', views.patients, name='patients'),
    path('patients/<path:folder>/', views.view_pngs, name='view_pngs'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
