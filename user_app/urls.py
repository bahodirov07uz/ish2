from django.contrib import admin
from django.urls import path,include
from .views import user_home,get_ish_chart_data,ishchi_chart_page
from django.conf import settings
from django.conf.urls.static import static

app_name = 'userapp'

urlpatterns = [
    path('', user_home, name='user_home'),
    path('chart/', ishchi_chart_page, name='chart_page'),
    path('chart/data/', get_ish_chart_data, name='ish_chart_data'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
