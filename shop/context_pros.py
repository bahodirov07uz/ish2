from .models import *
from django.shortcuts import render,get_object_or_404
from .views import get_image_hash,get_images_by_product_and_color
def cart_items(request):
    cart = request.session.get("cart", {})
    # a ={'id':1,'name':'aaaaa'}
    total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.values())   
    quantity =sum(int(item["quantity"]) for item in cart.values())
    return {"cartitem": cart,'total_price': total_price, 'quantity':quantity}


def avg_rating(request):
    products = Product.objects.all()
    avg_ratings = {product.id: Product.get_avg_rating(product.id) for product in products}
    return {'avg_ratings': avg_ratings}


def category_items(request):
    context = {}
    context['categories'] = Category.objects.all()
    return context


def categories_processor(request):
    return {'categories': Category.objects.all()}


def product_filter(request):
    queryset = Product.objects.all()

    filter_type = request.GET.get('filter', 'last_5') 
    if filter_type == 'last_5':
        queryset = queryset.order_by('-created_at')[:5] 
    elif filter_type == 'arzon':
        queryset = queryset.order_by('narxi')  # Narxi bo‘yicha arzonlari
    elif filter_type == 'qimmat':
        queryset = queryset.order_by('-narxi')  # Narxi bo‘yicha qimmatlari

    return {'filtered_products': queryset}