from django.contrib import admin
from django.urls import path,include
from .views import *
from .context_pros import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'shop'

urlpatterns = [
    path('',Homeview.as_view(),name='home'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('deals/', DealView.as_view(), name='deals'),
    path('wishlist/<int:product_id>/', add_to_wishlist_session, name='add_to_wishlist_session'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist_session, name='remove_from_wishlist_session'),
    path('cart/remove/<str:cart_key>/', remove_cart, name='remove_cart'),
    path('wishlist/get/', get_wishlist, name='get_wishlist'),
    path('add_to_cart/', add_to_cart, name='add_cart'),
    path('cart/', cart_view, name='cart'),
    path("create-order/", create_order, name="create_order"),
    path('ord/',OrderView.as_view(), name='ord'),
    path('order-detail/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    # path('category-filter/<int:id>/',category_view, name='category_filter'),
    path("order/cancel/<int:order_id>/", cancel_order, name="cancel_order"),
    path("bestsellers/", BestsellerListView.as_view(), name="bestsellers"),
    path('products/', product_list, name='product_list'),
    path("submit-review/<int:product_id>/", submit_review, name="submit_review"),
    path('search-suggestions/', search_suggestions, name='search_suggestions'),
    path('search/',search_view, name='search'),
    path('new-items/',new_products_view, name='news'),
    path('submit-rating/<int:product_id>/', submit_rating, name='submit_rating'),
    path('checkout', checkout, name='checkout'),
    path('faq/',faq, name='faq'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
