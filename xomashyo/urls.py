from django.contrib import admin
from django.urls import path,include
from .views import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'xomashyo'

urlpatterns = [
    path('',XomashyoView.as_view(),name='x_view'),
    path('xomashyo-form/',Xomashyoqabul,name='xomashyo_qabul'),
    path('xomashyolar/pdf/', XomashyoPDFView.as_view(), name='xomashyo_pdf'),
    path('xomashyo-harakatlari/pdf/', XomashyoHarakatPDFView.as_view(), name='xomashyo_harakat_pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
