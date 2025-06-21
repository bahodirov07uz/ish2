from django.contrib import admin
from django.urls import path,include
from .views import user_home 
from django.conf import settings
from django.conf.urls.static import static

app_name = 'userapp'

urlpatterns = [
    path('', user_home, name='user_home'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
