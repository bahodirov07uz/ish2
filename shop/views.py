from django.shortcuts import render , get_object_or_404, redirect
from django.views.generic import ListView,DetailView
from .models import *
from django.utils.timezone import now
from django.db.models import Sum,F
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth,TruncWeek
from datetime import date,datetime,timedelta
from django.http import JsonResponse
import hashlib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import *
from django.utils import timezone
import logging
def get_image_hash(image):
    """Rasm faylining hash qiymatini qaytaradi"""
    hasher = hashlib.sha256()
    for chunk in image.file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()

def get_images_by_product_and_color():
    # Mahsulot variantlarini mahsulot va ranglar bo'yicha guruhlash
    products_with_colors = ProductVariant.objects.values('product', 'color').distinct()

    images_by_product_and_color = {}

    for item in products_with_colors:
        product_id = item['product']  # Bu yerda product.id ni olishimiz kerak
        color = item['color']

        # Har bir mahsulot va rang uchun birinchi variantning rasmini olish
        product_variant = ProductVariant.objects.filter(product_id=product_id, color=color).first()

        if product_variant and product_variant.image:
            if product_id not in images_by_product_and_color:
                images_by_product_and_color[product_id] = {}
            images_by_product_and_color[product_id][color] = product_variant.image.url

    return images_by_product_and_color


class Homeview(ListView):
    template_name = 'shop/home.html'
    model = Product
    context_object_name = 'products'
    def get_queryset(self):
        category_name = self.kwargs.get("category_name")
        if category_name:
            return Product.objects.filter(category__name=category_name)
        return Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all().order_by('-id')

        # Mahsulotlar va ularning variantlarini olish
        images_by_product_and_color = get_images_by_product_and_color()


        for product in context['products']:
            product.colors = list(product.variants.values_list('color', flat=True).distinct())
            product.sizes = list(set(product.variants.values_list('size', flat=True)))

            # Mahsulotga ranglar va rasmlar qo'shish
            product.image_by_color = images_by_product_and_color.get(product.id, {})

        context['images_by_product_and_color'] = images_by_product_and_color
        # category =  Category.objects.filter(name = 'krossovka')
        # a= Product.objects.filter(category=category)
        return context





class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/single-product.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # Mahsulot va variantlarni olish
        images_by_product_and_color = get_images_by_product_and_color()

        product.colors = list(product.variants.values_list('color', flat=True).distinct())
        product.sizes = list(product.variants.values_list('size', flat=True).distinct())
        product.image_by_color = images_by_product_and_color.get(product.id, {})

        context['product'] = product  # Contextga asosiy mahsulotni qo'shish
        context['last'] = Product.objects.all().order_by('-id')[:4]
        context['images_by_product_and_color'] = images_by_product_and_color
        context['comments'] = Comment.objects.filter(product_id=product.id)
        context['modal_products'] = Product.objects.all()

        return context

class DealView(ListView):
    template_name ='shop/deal.html'
    model = Product
    context_object_name = 'mhst'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all().order_by('-id')

        # Mahsulotlar va ularning variantlarini olish
        images_by_product_and_color = get_images_by_product_and_color()


        for product in context['products']:
            product.colors = list(product.variants.values_list('color', flat=True).distinct())
            product.sizes = list(set(product.variants.values_list('size', flat=True)))

            # Mahsulotga ranglar va rasmlar qo'shish
            product.image_by_color = images_by_product_and_color.get(product.id, {})

        context['images_by_product_and_color'] = images_by_product_and_color

        return context

    def get_queryset(self):
        products = Product.objects.all()

        filter_type = self.request.GET.get('filter','last_5')

        if filter_type == 'last_51':
            return products.order_by('-created_at')[:5]
        elif filter_type == 'arzon1':
            return products.order_by('narxi')
        elif filter_type == 'qimmat1':
            return products.order_by('-narxi')
        return products

def add_to_wishlist_session(request, product_id):
    if "wishlist" not in request.session:
        request.session["wishlist"] = []

    wishlist = request.session["wishlist"]
    if product_id not in wishlist:
        wishlist.append(product_id)
        request.session["wishlist"] = wishlist
        request.session.modified = True
        return JsonResponse({"message": "Mahsulot wishlist-ga qo‘shildi!"})
    else:
        return JsonResponse({"message": "Mahsulot allaqachon wishlistda!"})


def remove_from_wishlist_session(request, product_id):
    wishlist = request.session.get("wishlist", [])

    if product_id in wishlist:
        wishlist.remove(product_id)
        request.session["wishlist"] = wishlist  # Sessionni yangilash
        return JsonResponse({"message": "Mahsulot wishlist-dan olib tashlandi!"})

    return JsonResponse({"message": "Mahsulot wishlist-da yo‘q!"})

def get_wishlist(request):
    wishlist = request.session.get("wishlist", [])
    products = Product.objects.filter(id__in=wishlist)
    return render(request,'shop/wishlist.html',{"product": products})

def faq(request):
    return render(request,'shop/faq.html')
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        color = request.POST.get("color")
        size = request.POST.get("size")
        siaze = request.POST.get("selected_size")
        name = request.POST.get("product_name")
        quantity = int(request.POST.get("quantity"))
        variant = request.POST.get('variant_id')
        price = request.POST.get("cartnarx")
        cart = request.session.get("cart", {})
        product = Product.objects.get(id=int(product_id))
        print(f'asdfghjk {variant}')
        print(f'asdfghjk {size}')
        print(f'asdfghjk {color}')
        variants = ProductVariant.objects.get(id=int(variant))
        matching_variant = ProductVariant.objects.filter(product=product, size=size, color=color).first()
        print(matching_variant)
        rasm = matching_variant.image.url

        cart_key = f"{product_id}_{color}_{size}"

        if cart_key in cart:
            cart[cart_key]["quantity"] += quantity

        else:
            cart[cart_key] = {
                "product_id": product_id,
                "color": color,
                "size": size,
                "name": name,
                "quantity": quantity,
                'image': rasm,
                'price': float(price),
                'variant_id': variant,
                'total_price' :int(quantity) * (price)
            }



        request.session["cart"] = cart
        request.session.modified = True

        return redirect('shop:home')

    return redirect("shop:home")



class BestsellerListView(ListView):
    model = Product
    template_name = "shop/custom-deal-page.html"
    context_object_name = "bestsellers"

    def get_queryset(self):
        best_selling_products = (
            OrderItem.objects.values("product")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:10]
        )

        product_ids = [item["product"] for item in best_selling_products]

        products = Product.objects.filter(id__in=product_ids)

        filter_type = self.request.GET.get('filter','last_5')

        if filter_type == 'last_51':
            return products.order_by('-created_at')[:5]
        elif filter_type == 'arzon1':
            return products.order_by('narxi')
        elif filter_type == 'qimmat1':
            return products.order_by('-narxi')

        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bestsellers"] = self.get_queryset()
        return context


def remove_cart(request, cart_key):
    cart = request.session.get("cart", {})

    if cart_key in cart:
        del cart[cart_key]
        request.session["cart"] = cart
        request.session.modified = True
        return JsonResponse({"message": "Mahsulot muvaffaqiyatli o‘chirildi!"})

    return JsonResponse({"message": "Mahsulot topilmadi yoki allaqachon o‘chirib tashlangan!"})

def cart_view(request):
    cart = request.session.get("cart", {})
    context = {}
    context['viloyat'] = Viloyat.objects.all()
    context['cart'] = request.session.get("cart", {})
    return render(request, "shop/cart.html",context)


@login_required
def create_order(request):

    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Savatchangiz bo‘sh!")

    if request.method == "POST" and 'sbmt' in request.POST:
        viloyat_id = request.POST.get("viloyat")
        addres = request.POST.get("shahar")
        postcode = request.POST.get("postcode")
        userr = request.user



        delivery = Delivery.objects.create(
            viloyat_id=viloyat_id,
            addres=addres,
            postcode=postcode,
            user=userr,

        )

        total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.values())
        user = request.user if request.user.is_authenticated else None
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            delivery_address=delivery
        )
        for item in cart.values():
            product_instance = Product.objects.get(id=item["product_id"])
            variants = ProductVariant.objects.get(id=item["variant_id"])
            matching_variant = ProductVariant.objects.filter(product=product_instance, size=item['size'], color=item['color']).first()

            orderitem = OrderItem.objects.create(
                order=order,
                product=product_instance,
                price=float(item["price"]),
                variant=matching_variant,
                quantity=int(item["quantity"]),
                image=matching_variant.image,
            )
            variant = product_instance.variants.first()

            if not matching_variant:
                raise ValueError(f"{orderitem.product.nomi} uchun variant mavjud emas!")

            if matching_variant.stock >= orderitem.quantity:
                matching_variant.stock -= orderitem.quantity
                matching_variant.save()
            else:
                raise ValueError("Yetarlicha mahsulot mavjud emas!")



    request.session["cart"] = {}
    request.session.modified = True


    messages.success(request, "Buyurtmangiz muvaffaqiyatli yaratildi!")
    return redirect("shop:cart")

def checkout(request):
    return render(request,'shop/checkout.html')



class OrderView(ListView):
    template_name = 'shop/dash-my-order.html'
    model = Order

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        filter_type = self.request.GET.get('filter','last_5')

        if filter_type == 'last_5':
            return queryset.order_by('-created_at')[:5]
        elif filter_type == 'Kutilmoqda':
            return queryset.filter(status='Kutilmoqda')
        elif filter_type == 'Bekor qilindi':
            return queryset.filter(status='Bekor qilindi')
        elif filter_type == 'Yetkazib berildi':
            return queryset.filter(status='Yetkazib berildi')
        elif filter_type == 'Yetkazib berilyapti':
            return queryset.filter(status='Yetkazib berilyapti')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['orders'] = Order.objects.filter(user=self.request.user)
        context['cancelled']  = Order.objects.filter(user=self.request.user, status='Bekor qilindi')

        return  context



class OrderDetailView(DetailView):
    template_name = 'shop/order-detail.html'
    model = Order
    context_object_name = 'order'





def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.can_be_cancelled():
        order.status = "Bekor qilindi"
        order.save()
        return JsonResponse({"message": "Buyurtma bekor qilindi!"})
    else:
        return JsonResponse({"error": "Bu buyurtmani bekor qilib bo‘lmaydi!"}, status=400)



def get_wishlist(request):
    wishlist = request.session.get("wishlist", [])
    products = Product.objects.filter(id__in=wishlist)
    return render(request,'shop/wishlist.html',{"product": products})

def product_list(request):
    category_id = request.GET.get('category')  # URL'dan kategoriya ID olamiz
    products = Product.objects.all()  # Barcha mahsulotlarni olamiz

    if category_id:
        context = {}
        context['products'] = Product.objects.all().order_by('-id')
        products = products.filter(category_id=category_id)
        context['product'] = products.filter(category_id=category_id)

        # Mahsulotlar va ularning variantlarini olish
        images_by_product_and_color = get_images_by_product_and_color()


        for product in context['products']:
            product.colors = list(product.variants.values_list('color', flat=True).distinct())
            product.sizes = list(set(product.variants.values_list('size', flat=True)))

            # Mahsulotga ranglar va rasmlar qo'shish
            product.image_by_color = images_by_product_and_color.get(product.id, {})

        context['images_by_product_and_color'] = images_by_product_and_color


    return render(request, 'shop/categoroy.html',context)


from django.http import JsonResponse

@login_required
def submit_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        text = request.POST.get("text")
        rating = request.POST.get("rating")

        if not text or not rating:
            return JsonResponse({"success": False, "message": "Sharh matni va reyting talab qilinadi!"})

        try:
            review = Comment.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                text=text
            )
            review.save()
            return JsonResponse({"success": True, "message": "Sharhingiz muvaffaqiyatli qo‘shildi!"}, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Xatolik yuz berdi: {str(e)}"})

    return JsonResponse({"success": False, "message": "Faqat POST so‘rovga ruxsat berilgan!"})


    return JsonResponse({"success": False, "message": "Noto‘g‘ri so‘rov."})


def search_view(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    products = Product.objects.all()

    if query:
        products = products.filter(nomi__icontains=query)

    images_by_product_and_color = get_images_by_product_and_color()

    for product in products:
        product.colors = list(product.variants.values_list('color', flat=True).distinct())
        product.sizes = list(set(product.variants.values_list('size', flat=True)))
        product.image_by_color = images_by_product_and_color.get(product.id, {})

    context = {
        'products': products,
        'query': query,
        'category': category,
        'images_by_product_and_color': images_by_product_and_color,  # Oldin yo‘qotilgan qism
    }

    return render(request, 'shop/search_results.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(nomi__icontains=query)[:5]
    suggestions = [{'name': product.nomi} for product in products]
    return JsonResponse({'suggestions': suggestions})


def new_products_view(request):
    one_week_ago = now() - timedelta(days=7)
    category = request.GET.get('category', '')

    new_products = Product.objects.filter(created_at__gte=one_week_ago)

    images_by_product_and_color = get_images_by_product_and_color()

    for product in new_products:
        product.colors = list(product.variants.values_list('color', flat=True).distinct())
        product.sizes = list(set(product.variants.values_list('size', flat=True)))
        product.image_by_color = images_by_product_and_color.get(product.id, {})


    if category:
        new_products = new_products.filter(category__id=category)

    context = {
        'new_products': new_products,
        'sel_category': category,
        'images_by_product_and_color': images_by_product_and_color,
    }

    return render(request,'shop/news.html', context)

@login_required
def submit_rating(request, product_id):
    if request.method == 'POST':
        rating_value = int(request.POST.get('rating'))
        product = get_object_or_404(Product, id=product_id)

        # Foydalanuvchi avval baho berganmi, tekshiramiz
        rating, created = Rating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating_value}
        )

        return JsonResponse({'success': True, 'rating': rating_value})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

