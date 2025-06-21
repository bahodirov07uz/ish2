from django.contrib import admin
from django.urls import path,include
from .views import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'main'

urlpatterns = [
    path('',Home,name='home'),
    path('detail/<int:pk>',DetailView.as_view(),name='detail'),
    path('oylik_yopish/<int:pk>/', oylik_yopish, name='oylik_yopish'),
    path('yangi_oy_boshlash/<int:pk>/',yangi_oy_boshlash, name='yangi_oy'),
    path('forms/',FormView.as_view(), name='forms'),
    path('billing/',billing, name='billing'),
    path('api/weekly-sales/', get_weekly_sales, name='weekly_sales_api'),
    path('tables/',TableView.as_view(), name='tables'),
    path('crete_frm/',create_model, name='crete_frm'),
    path('orders-page/',JadvalView.as_view(), name='order'),
    path('order-detail/<int:pk>/',OrderDtlView.as_view(), name='order_detail'),
    path('variant-detail/<int:pk>/',VariantDetailView.as_view(), name='variant_detail'),
    path('jadvallar/',JadvalView.as_view(), name='jadval'),
    path('xaridor-detail/<int:pk>/',XaridorDetailView.as_view(),name='xaridor_detail'),
    path("update-product/<int:product_id>/", update_product, name="update_product"),
    path("yangilash-statusni/", update_status, name="update_status"),
    path('api/top-products/', top_selling_products, name='top_products'),
    path('add-ish/', add_ish, name='add_ish'),
    path('edit-tables/<int:pk>',edit_tables ,name='edit_table'),
    path('api/monthly-sales/', get_monthly_sales, name='monthly_sales'),
    path('products/delete/<int:pk>/', delete_product, name='delete_product'),
    path('api/weekly-works/', get_weekly_work_summary, name='weekly-sales-works'),
    path('ish-request/create/', IshRequestCreateView.as_view(), name='ish_request_create'),
    path('ish-request/list/', IshRequestListView.as_view(), name='ish_request_list'),
    path('ish-request/<int:pk>/', IshRequestDetailView.as_view(), name='ish_request_detail'),
    path('ish-request/<int:pk>/update/', IshRequestUpdateView.as_view(), name='ish_request_update'),    
    # Tasdiqlash/Rad etish
    path('ish-request/<int:pk>/approve/', approve_ish_request, name='ish_request_approve'),
    path('ish-request/<int:pk>/reject/', reject_ish_request, name='ish_request_reject'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)