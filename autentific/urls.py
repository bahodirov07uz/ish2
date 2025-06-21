from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from .views import login_page,register_view,custom_logout
app_name = 'autentific'
urlpatterns = [
    path('',login_page, name='login_page'),
    path('secret-register/',register_view,name='register_page'),
    path('secret-logout/', custom_logout, name='logout'),
]   

