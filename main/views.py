from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .models import * 
from django.shortcuts import render, get_object_or_404,redirect
from django.utils.timezone import now
from django.utils import timezone
from django.db.models import Sum,F,Count,ExpressionWrapper, IntegerField
from django.db.models.functions import TruncMonth,TruncWeek
from datetime import date,datetime,timedelta
from django.http import JsonResponse
from django.contrib import messages
from shop.views import get_images_by_product_and_color
from shop.models import Order,OrderItem,Product,ProductVariant
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from collections import defaultdict 
from django.contrib.auth.decorators import user_passes_test,login_required
from django.views.decorators.csrf import csrf_exempt
import calendar
from .forms import IshRequestForm
from django.urls import reverse_lazy
from django.db.models.functions import ExtractWeek, ExtractYear

def is_admin(user):
    return user.is_staff

def Home(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('autentific:login_page') 
    if user.is_superuser or user.is_staff:
        context = {}
        today = datetime.now()
        
        # Joriy oy vaqt oralig'i
        current_month_start = datetime(today.year, today.month, 1)
        _, last_day = calendar.monthrange(today.year, today.month)
        current_month_end = current_month_start + timedelta(days=last_day)
        
        # Oldingi oy vaqt oralig'i
        previous_month = current_month_start - timedelta(days=1)
        previous_month_start = previous_month.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)

        # Kirim (sales) statistikasi
        current_sales = Kirim.objects.filter(
            sana__gte=current_month_start, 
            sana__lt=current_month_end
        ).aggregate(
            total_quantity=Sum('quantity'),
            total_sum=Sum('summa')
        )
        
        previous_sales = Kirim.objects.filter(
            sana__gte=previous_month_start, 
            sana__lte=previous_month_end
        ).aggregate(
            total_quantity=Sum('quantity'),
            total_sum=Sum('summa')
        )

        # Order va OrderItem statistikasi (sizning order_statistics() funksiyangiz)
        current_orders = Order.objects.filter(
            created_at__gte=current_month_start,
            created_at__lt=current_month_end
        ).count()
        
        previous_orders = Order.objects.filter(
            created_at__gte=previous_month_start,
            created_at__lte=previous_month_end
        ).count()

        current_order_items = OrderItem.objects.filter(
            order__created_at__gte=current_month_start,
            order__created_at__lt=current_month_end
        ).count()   
        
        previous_order_items = OrderItem.objects.filter(
            order__created_at__gte=previous_month_start,
            order__created_at__lte=previous_month_end
        ).count()

        # Foiz o'zgarishini hisoblash funksiyasi
        def calculate_percentage_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)

        # Kontekstni to'ldirish
        context.update({
            # Sales statistikasi
            'current_sales_total': current_sales['total_quantity'] or 0,
            'previous_sales_total': previous_sales['total_quantity'] or 0,
            'current_sales_sum': current_sales['total_sum'] or 0,
            'previous_sales_sum': previous_sales['total_sum'] or 0,
            'foiz': calculate_percentage_change(
                current_sales['total_quantity'] or 0, 
                previous_sales['total_quantity'] or 0
            ),
            'total_turnover': Kirim.objects.aggregate(total=Sum('summa'))['total'] or 0,
            
            # Order statistikasi
            'current_orders': current_orders,
            'previous_orders': previous_orders,
            'order_change': calculate_percentage_change(current_orders, previous_orders),
            'current_order_items': current_order_items,
            'previous_order_items': previous_order_items,
            'order_item_change': calculate_percentage_change(current_order_items, previous_order_items),
            
            # Boshqa statistikalar
            'total_': Ish.objects.aggregate(total=Sum('soni'))['total'] or 0,
            'total_item': Kirim.objects.aggregate(total_item=Sum('quantity'))['total_item'] or 0,
            'total_sum': Chiqim.sum_prices(),
            'soni': Ishchi.objects.count(),
            'ish_soni': Product.objects.aggregate(Sum('soni'))['soni__sum'] or 0,
            'oy_nomi': previous_month_start.strftime('%B'),
            'ishchilar': Ishchi.objects.all(),
            'chiqimlar': Chiqim.objects.order_by('-id')[:3],
            'users': CustomUser.objects.all(),
            'products': Product.objects.all(),
        })
        
        return render(request, 'dashboard.html', context)
    elif hasattr(user, 'ishchi_profile') or user.is_ishchi:
        return redirect('userapp:user_home')
    return redirect('shop:home')

@user_passes_test(is_admin)  
def oylik_yopish(request, pk):
    """
    Ishchi uchun joriy oylikni yopadi va oylik ma'lumotlarini Oyliklar modeliga saqlaydi.
    """
    ishchi = get_object_or_404(Ishchi, pk=pk)

    if request.method == "POST":
        if not ishchi.is_oylik_open:
            return redirect('main:detail', pk=pk)

        umumiy_oylik = sum(ish.narxi for ish in Ish.objects.filter(ishchi=ishchi))
        ishlari = Ish.objects.filter(ishchi=ishchi)


        oylik_yozuv =Oyliklar.objects.create(
            ishchi=ishchi,
            oylik=umumiy_oylik,
            yopilgan=True
        )

        for ish in ishlari:
            EskiIsh.objects.create(
                ishchi=ish.ishchi,
                mahsulot= ish.mahsulot.nomi,
                soni=ish.soni,
                sana=ish.sana,
                narxi=ish.narxi,
                ishchi_oylik = oylik_yozuv
            
            )                               
            
        ishchi.oldingi_oylik = umumiy_oylik
        ishchi.is_oylik_open = False
        ishchi.save()

        Ish.objects.filter(ishchi=ishchi).delete()

    return redirect('main:detail', pk=pk)

@user_passes_test(is_admin)  
def yangi_oy_boshlash(request, pk):
    """
    Yangi oylikni yaratadi va uni Ishchi modeliga bog'laydi.
    """
    ishchi = get_object_or_404(Ishchi, pk=pk)

    if request.method == "POST":

        if ishchi.is_oylik_open:
            return redirect('main:detail', pk=pk)

        ishchi.is_oylik_open = True
        ishchi.save()

    return redirect('main:detail', pk=pk)

class FormView(LoginRequiredMixin,ListView):
    template_name = 'form.html'
    model = Ishchi
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # category
        categories = Category.objects.all()
        for category in categories:
            category.ishchilar_soni = category.ish_turi.count()
        context['categories'] = categories
        context['ishchilar'] = Ishchi.objects.all()
        context['mahsulot'] = Product.objects.all()
        context['xaridor'] =Xaridor.objects.all()
        context['chiqimturi'] = ChiqimTuri.objects.all()

        return  context
    

@user_passes_test(is_admin)  
def billing(request):

    context = {}

    today = datetime.now()
    current_month_start = datetime(today.year, today.month, 1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    def calculate_percentage_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)
    current_month_chiqim = Chiqim.objects.filter(
        created__gte=current_month_start
    ).aggregate(total=Sum('price'))['total'] or 0

    last_month_chiqim = Chiqim.objects.filter(
        created__gte=last_month_start,
        created__lte=last_month_end
    ).aggregate(total=Sum('price'))['total'] or 0

    total_sum = Kirim.objects.filter(sana__gte=current_month_start).aggregate(total_sum=Sum(F('quantity') * F('mahsulot__narxi')))

    xaridorlar = Xaridor.objects.annotate(
        total_sales=Sum('kirimlar__summa')
    ).order_by('-total_sales')
    context['xaridorlar'] = xaridorlar

    kategoriya_boyicha_ishlar = Category.objects.annotate(
        umumiy_soni=Sum('ish_turi__ishlar__soni')
    ).values('nomi', 'umumiy_soni')

    category_data = {item['nomi']: item['umumiy_soni'] or 0 for item in kategoriya_boyicha_ishlar}

    # foyda hisoblash
    total_chiqim = Chiqim.objects.filter(created__gte=current_month_start).aggregate(total_chiqim=Sum(F('price')))['total_chiqim'] or 0 
    total_kirim = Kirim.objects.filter(sana__gte=current_month_start).aggregate(total_kirim=Sum(F('summa')))['total_kirim'] or 0
    jami_oyliklar = Oyliklar.objects.filter(
        sana__year=today.year, sana__month=today.month
    ).aggregate(total=Sum('oylik'))['total'] or 0 

    top_by_sum = Xaridor.objects.annotate(
        total_spent=Sum('kirimlar__summa')
    ).order_by('-total_spent').first()

    top_by_quantity = Xaridor.objects.annotate(
        total_quantity=Sum('kirimlar__quantity')
    ).order_by('-total_quantity').first()
    
    ishlar = Ish.objects.annotate(
        umumiy=ExpressionWrapper(
            F('narxi'),
            output_field=IntegerField()
        )
    )
    total_oyliklar = ishlar.aggregate(jami=Sum('umumiy'))['jami']

    foyda = total_kirim - total_chiqim - jami_oyliklar
    context['total_oyliklar'] = total_oyliklar
    context['last_month_chiqim'] = last_month_chiqim
    context['current_month_chiqim'] = current_month_chiqim
    context['last_chiqim_foiz'] = calculate_percentage_change(current_month_chiqim,last_month_chiqim)

    context['top_by_sum'] = top_by_sum
    context['top_by_quantity'] = top_by_quantity
    context['oy'] = current_month_start
    context['foyda'] = foyda
    context['xaridor'] = Xaridor.objects.all()
    context['kirim'] = Kirim.objects.all().order_by('-id')
    context['umumiy_kosib'] = category_data.get('kosib', 0)
    context['umumiy_z'] = category_data.get('zakatovka',0)
    context['umumiy_k'] = category_data.get('kroy',0)
    context['total_sum'] = total_sum['total_sum']
    


    return render(request, 'billing.html', context)


@user_passes_test(is_admin)  
def get_weekly_sales(request):
    today = now().date()
    start_date = today - timedelta(weeks=7)

    # Kirim bo‘yicha sotuvlar
    kirim_sales = Kirim.objects.filter(sana__gte=start_date).annotate(
        week_start=TruncWeek('sana')
    ).values('week_start').annotate(
        total_sales=Sum('quantity')
    ).order_by('week_start')

    # Berilgan orderlar soni
    order_sales = Order.objects.filter(created_at__gte=start_date).annotate(
        week_start=TruncWeek('created_at')
    ).values('week_start').annotate(
        total_orders=Count('id')
    ).order_by('week_start')

    # Ma’lumotlarni yig‘ish
    labels = []
    kirim_data = []
    order_data = []

    current_date = start_date
    while current_date <= today:
        week_start = current_date - timedelta(days=current_date.weekday())  # Hafta boshlanish sanasi
        week_end = week_start + timedelta(days=6)  # Hafta tugash sanasi

        kirim_week = next((sale for sale in kirim_sales if sale['week_start'].date() >= week_start and sale['week_start'].date() <= week_end), None)
        order_week = next((sale for sale in order_sales if sale['week_start'].date() >= week_start and sale['week_start'].date() <= week_end), None)

        labels.append(f"{week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
        kirim_data.append(kirim_week['total_sales'] if kirim_week else 0)
        order_data.append(order_week['total_orders'] if order_week else 0)

        current_date += timedelta(weeks=1)  # Keyingi haftaga o'tish

    return JsonResponse({'labels': labels, 'kirim_data': kirim_data, 'order_data': order_data}) 

def get_monthly_sales(request):
    today = now().date()
    start_date = today - timedelta(days=90)  # Oxirgi 3 oy ma'lumoti
    
    # Kirim bo'yicha oylik sotuvlar
    kirim_sales = Kirim.objects.filter(sana__gte=start_date).annotate(
        month=TruncMonth('sana')
    ).values('month').annotate(
        total_sales=Sum('quantity')
    ).order_by('month')
    
    # Order bo'yicha oylik buyurtmalar
    order_sales = Order.objects.filter(created_at__gte=start_date).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_orders=Count('id')
    ).order_by('month')
    
    # Ma'lumotlarni yig'ish
    labels = []
    kirim_data = []
    order_data = []
    
    current_date = start_date.replace(day=1)  # Oyning birinchi kuni
    while current_date <= today:
        month_start = current_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        kirim_month = next((sale for sale in kirim_sales if sale['month'].date() == month_start), None)
        order_month = next((sale for sale in order_sales if sale['month'].date() == month_start), None)
        
        labels.append(month_start.strftime('%Y-%m'))
        kirim_data.append(kirim_month['total_sales'] if kirim_month else 0)
        order_data.append(order_month['total_orders'] if order_month else 0)
        
        # Keyingi oyga o'tish
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year+1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month+1)
    
    return JsonResponse({
        'labels': labels,
        'kirim_data': kirim_data,
        'order_data': order_data
    })

class TableView(LoginRequiredMixin,ListView):
    template_name = 'tables.html'
    model = Product
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variant'] = ProductVariant.objects.all()
        products = Product.objects.all()
        unique_variants = []

        for product in products:
            product.produce = Ish.objects.filter(mahsulot=product).count()
            product.all_produce = EskiIsh.objects.filter(mahsulot=product)
            
            seen_colors = set()  
            for variant in product.variants.all():
                if variant.color not in seen_colors:
                    unique_variants.append(variant)
                    seen_colors.add(variant.color)
        context['products'] = products
        context['unique_variants'] = unique_variants
        return context   
        
class VariantDetailView(LoginRequiredMixin,DetailView):
    template_name = 'variant-detail.html'
    model = Product
    context_object_name = 'variant'


class OrderDtlView(LoginRequiredMixin,DetailView):
    template_name = 'order-detail.html'
    model = Order
    context_object_name = 'order'

class XaridorDetailView(LoginRequiredMixin,DetailView):
    template_name = 'xaridor_detail.html'
    model = Xaridor
    context_object_name = 'xaridor'
    
@user_passes_test(is_admin)  
def create_model(request):
    if request.method == 'POST':
        if 'ish_qosh' in request.POST:
            ism = request.POST.get('ish_mahsulot')
            soni = request.POST.get('ish_soni')
            narxi = request.POST.get('ish_narxi')
            ishchi = request.POST.get('ish_name')

            Ish.objects.create(
                mahsulot_id=ism,
                soni=soni,
                narxi=narxi,
                ishchi_id=ishchi,
            )
            messages.success(request, 'Ish muvaffaqiyatli qo‘shildi!')


            ishchii = Ishchi.objects.get(id=ishchi)
            if ishchii.turi.nomi == 'kosib':
                mahsulot = Product.objects.get(id=ism)
                mahsulot.soni += int(soni)

                variants = mahsulot.variants.all()
                if variants.exists():
                    each_variant_increase = int(soni) // variants.count()  # Har bir variant uchun qo‘shiladigan miqdor
                    for variant in variants:
                        variant.stock += each_variant_increase
                        variant.save()
                    mahsulot.save()

        elif 'sotuv' in request.POST:
            xaridor = request.POST.get('sotuv_name')
            mahsulot = request.POST.get('sotuv_mahsulot')
            soni = int(request.POST.get('sotuv_soni', 0))

            kirim =Kirim.objects.create(
                xaridor_id=xaridor,
                mahsulot_id=mahsulot,
                quantity=soni,
            )
            messages.success(request, 'Sotuv muvaffaqiyatli amalga oshirildi!')

        elif 'chiqim' in request.POST:
            nomi = request.POST.get('chiqim_name')
            narxi = request.POST.get('chiqim_narxi')
            turi = request.POST.get('chiqimturi')

            Chiqim.objects.create(
                name=nomi,
                price=narxi,
                category_id=turi,
            )
            messages.success(request, 'Chiqim muvaffaqiyatli qo‘shildi!')

        elif 'mahs_sbmt' in request.POST:
            nomi = request.POST.get('mahsulot_nomi')
            narxi = request.POST.get('mahsulot_narxi')
            soni = request.POST.get('mahsulot_soni')
            rasm = request.FILES.get('mahsulot_rasmi') 

            Product.objects.create(
                nomi=nomi,
                narxi=narxi,
                soni=soni,
                image=rasm,
            )
            messages.success(request, 'Mahsulot muvaffaqiyatli qo‘shildi!')

        elif 'ctg_sbmt' in request.POST:
            nomi = request.POST.get('category_name')

            Category.objects.create(nomi=nomi)
            messages.success(request, 'Kategoriya muvaffaqiyatli qo‘shildi!')

        elif 'ishchi_sbmt' in request.POST:
            ism = request.POST.get('ishchi_name')
            faml = request.POST.get('ishchi_fam')
            tel = request.POST.get('ishchi_tel')
            ctg = request.POST.get('ish_ctg')

            Ishchi.objects.create(
                ism=ism,
                familiya=faml,
                telefon=tel,
                category_id=ctg,
            )
            messages.success(request, 'Ishchi muvaffaqiyatli qo‘shildi!')

        elif 'xar_sbmt' in request.POST:
            ism = request.POST.get('xar_name')
            tel = request.POST.get('xar_tel')

            Xaridor.objects.create(
                name=ism,
                telefon=tel,
            )
            messages.success(request, 'Xaridor muvaffaqiyatli qo‘shildi!')

        elif 'vrt_sbmt' in request.POST:
            rang = request.POST.get('variant_rang')  
            mahsulot = request.POST.get('variant_mahsulot')  
            stock = int(request.POST.get('variant_soni', 0))
            narxi = int(request.POST.get('variant_narxi'))
            rasm = request.FILES.get('variant_rasmi')
            sizes = ["39", "40", "41", "42", "43"]
            each_size_stock = stock // len(sizes)
            mahst = Product.objects.get(id=mahsulot)
            mhsoni = mahst.soni

            for size in sizes:
                variant, created = ProductVariant.objects.get_or_create(
                    product_id=mahsulot,
                    color=rang,
                    size=size,
                    price=narxi,
                    defaults={'stock': each_size_stock},
                    image=rasm
                )

                son = mhsoni  - (each_size_stock*len(sizes))
                Product.objects.filter(id=mahsulot).update(soni=son)


                if not created:
                    variant.stock += each_size_stock
                    variant.save()


        return redirect('main:forms')

    return render(request, 'form.html')

class DetailView(LoginRequiredMixin,DetailView):
    model = Ishchi
    template_name = 'table.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ishlar'] = Ish.objects.filter(ishchi=self.object)
        return context
    
class JadvalView(ListView):
    template_name = 'jadval.html'
    model = Order

    def get_queryset(self):
        queryset = Order.objects.all().order_by('-id')
        filter_type = self.request.GET.get('filter','hammasi') 
        viloyat_filter = self.request.GET.get('viloyat','all')
        if filter_type == 'last_5':
            if viloyat_filter == 'andijon':
                return queryset.filter(delivery_address__viloyat= 4)
            return queryset.order_by('-created_at')[:5] 
        elif filter_type == 'Hammasi':
            return queryset.order_by('-id')
        elif filter_type == 'Kutilmoqda':
            return queryset.filter(status='Kutilmoqda')
        elif filter_type == 'Bekor qilindi':
            return queryset.filter(status='Bekor qilindi') 
        elif filter_type == 'Yetkazib berildi':
            return queryset.filter(status='Yetkazib berildi')
        elif filter_type == 'Yetkazib berilyapti':
            return queryset.filter(status='Yetkazib berilyapti')

        return queryset

def update_product(request, product_id):
    if request.method == "POST":
        field = request.POST.get("field")  # O'zgarayotgan maydon nomi
        value = request.POST.get("value")  # Yangi qiymat

        product = get_object_or_404(Product, id=product_id)  # Mahsulotni topamiz

        if field and hasattr(product, field):  # Agar maydon mavjud bo‘lsa
            setattr(product, field, value)  # Ma'lumotni yangilash
            product.save()  # Saqlash
            return JsonResponse({"status": "success", "message": "Ma'lumot saqlandi!"})

        return JsonResponse({"status": "error", "message": "Noto‘g‘ri maydon!"}, status=400)

    return JsonResponse({"status": "error", "message": "Faqat POST so‘rovi qabul qilinadi!"}, status=405)

def update_status(request):
    if request.method == "POST":
        order_id = request.POST.get("id")
        new_status = request.POST.get("status")

        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            return JsonResponse({"success": True})
        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Order not found"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})

def top_selling_products(request):
    data = (
        OrderItem.objects.values('product__nomi')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )
    
    # Agar mahsulot nomi bo'sh bo'lsa, "Noma'lum" deb qo'yish
    formatted_data = []
    for item in data:
        product_name = item['product__nomi'] or "Noma'lum"
        formatted_data.append({
            'product__nomi': product_name,
            'total_sold': item['total_sold']
        })
    
    return JsonResponse(formatted_data, safe=False)


@csrf_exempt
def add_ish(request):
    if request.method == "POST":
        try:
            data = request.POST
            ishchi = Ishchi.objects.get(id=data.get('ishchi_id'))
            mahsulot = Product.objects.get(id=data.get('mahsulot_id'))
            soni = int(data.get('soni', 1))
            
            narx = mahsulot.get_price_for_category(ishchi.turi.nomi)
            
            Ish.objects.create(
                ishchi=ishchi,
                mahsulot=mahsulot,
                soni=soni,
                narxi=narx
            )

            return JsonResponse({
                "status": "success",
                "message": "Ish muvaffaqiyatli qo'shildi!",
                "narx": narx
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "status": "error",
        "message": "Faqat POST so'rovlari qabul qilinadi"
    }, status=405)

 
def edit_tables(request,pk):
    if request.method == 'POST':
        if 'delete' in request.POST:
            product = request.POST.get('product_id')
            objct = Product.objects.get(id=pk).delete(id=pk)
            objct.save()
    return render(request,'tables.html')

def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.nomi
        product.delete()
        messages.success(request, f'"{product_name}" mahsuloti muvaffaqiyatli o\'chirildi!')
        return redirect('main:tables')
    
    # Agar POST emas boshqa metod bilan so'rov qilinsa
    return redirect('main:tables')

def get_weekly_work_summary(request):
    # So'nggi 12 haftani olamiz
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=12)

    def fetch_data(model):
        return model.objects.filter(
            sana__range=(start_date, end_date)
        ).annotate(
            hafta=ExtractWeek('sana'),
            yil=ExtractYear('sana')
        ).values(
            'yil', 'hafta', 'ishchi__turi__nomi'
        ).annotate(
            total_soni=Sum('soni')
        )

    data = defaultdict(lambda: defaultdict(int))  # data[turi][hafta_label] = soni_sum

    for model in [Ish, EskiIsh]:
        for item in fetch_data(model):
            hafta_label = f"{item['yil']}-hafta{item['hafta']}"
            turi = item['ishchi__turi__nomi']
            data[turi][hafta_label] += item['total_soni'] or 0

    # Barcha haftalarni to‘plash (chiziqlar tekis chiqishi uchun)
    all_weeks = sorted({hafta for d in data.values() for hafta in d})

    # Rangi har tur uchun (ixtiyoriy)
    colors = {
        "kosib": "rgba(255, 99, 132, 1)",
        "zakatovka": "rgba(54, 162, 235, 1)",
        "kroy": "rgba(255, 206, 86, 1)",
        "pardozchi": "rgba(75, 192, 192, 1)",
    }

    # Chart.js formatida qaytaramiz
    response = {
        "labels": all_weeks,
        "datasets": []
    }

    for turi, weekly_data in data.items():
        response["datasets"].append({
            "label": turi,
            "data": [weekly_data.get(hafta, 0) for hafta in all_weeks],
            "borderColor": colors.get(turi, "rgba(100, 100, 100, 1)"),
            "backgroundColor": colors.get(turi, "rgba(100, 100, 100, 0.2)"),
            "borderWidth": 2,
            "fill": False,
            "tension": 0.4
        })

    return JsonResponse(response)

class IshRequestCreateView(LoginRequiredMixin, CreateView):
    model = IshRequest
    form_class = IshRequestForm
    template_name = 'requests/ish_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        if hasattr(self.request.user, 'ishchi_profile'):
            form.instance.ishchi = self.request.user.ishchi_profile
        form.save()
        messages.success(self.request, "Ish so'rovi muvaffaqiyatli yaratildi!")
        # Boshqa sahifaga redirect qilish o‘rniga, shu sahifani yangilab, bo‘sh form va message ko‘rsatamiz
        return render(self.request, self.template_name, {'form': self.form_class(user=self.request.user)})


class IshRequestListView(LoginRequiredMixin, ListView):
    model = IshRequest
    template_name = 'requests/ish_request_list.html'
    context_object_name = 'ish_requests'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Agar user superuser bo'lmasa, faqat o'z so'rovlarini ko'rsatish
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

class IshRequestDetailView(DetailView,LoginRequiredMixin):
    model = IshRequest
    template_name = 'requests/ish_request_detail.html'
    context_object_name = 'ish_request'

class IshRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = IshRequest
    form_class = IshRequestForm
    template_name = 'requests/ish_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Ish so'rovi muvaffaqiyatli yangilandi!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('main:ish_request_detail', kwargs={'pk': self.object.pk})


# Tasdiqlash va Rad etish funksiyalari
def approve_ish_request(request, pk):
    ish_request = get_object_or_404(IshRequest, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Sizda bu amalni bajarish uchun ruxsat yo'q!")
        return redirect('main:ish_request_list')
    
    ish_request.status = 'approved'
    ish_request.save()
    
    # Ish yaratish
    Ish.objects.create(
        mahsulot=ish_request.mahsulot,
        soni=ish_request.soni,
        sana=ish_request.sana,
        ishchi=ish_request.ishchi,
    )
    
    messages.success(request, "Ish so'rovi tasdiqlandi va ish yaratildi!")
    return redirect('main:ish_request_detail', pk=pk)

def reject_ish_request(request, pk):
    ish_request = get_object_or_404(IshRequest, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Sizda bu amalni bajarish uchun ruxsat yo'q!")
        return redirect('main:ish_request_list')
    
    ish_request.status = 'rejected'
    ish_request.save()
    messages.warning(request, "Ish so'rovi rad etildi!")
    return redirect('main:ish_request_detail', pk=pk)
