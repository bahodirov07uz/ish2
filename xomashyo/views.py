from django.shortcuts import render,redirect
from main.models import Xomashyo,XomashyoHarakat,YetkazibBeruvchi
from django.views.generic import ListView,View
from django.db.models import Q,Sum
from .utils import generate_xomashyo_pdf,generate_xomashyo_harakat_pdf
from datetime import datetime, timedelta

class XomashyoView(ListView):
    template_name = 'xomashyo.html'
    model = Xomashyo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        oylik_date  = today - timedelta(days=30)
        context['sum_price'] = XomashyoHarakat.objects.filter(sana__date__gte=oylik_date, harakat_turi='kirim').aggregate(Sum('narxi'))['narxi__sum']
        context['oylik_qaytarish'] = XomashyoHarakat.objects.filter(sana__date__gte=oylik_date, harakat_turi='qaytarish').count()
        context['oylik_qabul'] = XomashyoHarakat.objects.filter(sana__date__gte=oylik_date, harakat_turi='kirim').count()
        context['bugungi_qabul'] = XomashyoHarakat.objects.filter(sana__date=today, harakat_turi='kirim').count()
        context['xomashyos'] = Xomashyo.objects.all().order_by('-id')
        context['yetkazib_beruvchilar'] = YetkazibBeruvchi.objects.all()
        return context
    
def Xomashyoqabul(request):
    if request.method == 'POST':
        if 'kirim_btn' in request.POST:
            xomashyo_id = request.POST.get('name')
            yetkazib_beruvchi_id = request.POST.get('deliver')
            print(yetkazib_beruvchi_id)
            miqdor = int(request.POST.get('quantity'))
            narx = int(request.POST.get('price'))
            user = request.user
        
            
            xomashyo = Xomashyo.objects.get(id=xomashyo_id)

            # Xomashyo harakatini saqlash
            XomashyoHarakat.objects.create(
                xomashyo_id=xomashyo_id,
                yetkazib_beruvchi_id=yetkazib_beruvchi_id,
                harakat_turi='kirim',
                miqdori=miqdor,
                narxi=narx,
                foydalanuvchi=user,
            )
            
        return redirect('xomashyo:x_view')
    elif 'new_btn' in request.POST:
        nomi = request.POST.get('name')
        miqdori = request.POST.get('quantity')
        narxi = request.POST.get('price')
        minimal_miqdori = request.POST.get('min_quantity')
        o_lchov = request.POST.get('olchov')
        holati = request.POST.get('holat')
        yetkazib_beruvchi_id = request.POST.get('deliver')
        user = request.user
        # Yangi xomashyo yaratish
        xomashyo = Xomashyo.objects.create(
            nomi=nomi,
            miqdori=miqdori,
            narxi=narxi,
            olchov_birligi=o_lchov,
            holati=holati,
            minimal_miqdor = minimal_miqdori,
            yetkazib_beruvchi_id=yetkazib_beruvchi_id,
        )

    return render(request, 'xomashyo.html')



class XomashyoPDFView(View):
    def get(self, request):
        # Filtrlash imkoniyati (masalan, faqat active xomashyolar)
        queryset = Xomashyo.objects.filter(holati='active')
        
        # Qidiruv parametrlari
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(nomi__icontains=search))
        
        return generate_xomashyo_pdf(queryset)
    

class XomashyoHarakatPDFView(View):
    def get(self, request):
        # Asosiy queryset
        queryset = XomashyoHarakat.objects.select_related(
            'xomashyo', 'foydalanuvchi'
        ).order_by('-sana')
        
        # Filtrlash parametrlari
        xomashyo_id = request.GET.get('xomashyo_id')
        harakat_turi = request.GET.get('harakat_turi')
        sana_from = request.GET.get('sana_from')
        sana_to = request.GET.get('sana_to')
        
        # Filtrlarni qo'llash
        if xomashyo_id:
            queryset = queryset.filter(xomashyo_id=xomashyo_id)
        if harakat_turi:
            queryset = queryset.filter(harakat_turi=harakat_turi)
        if sana_from:
            sana_from = datetime.strptime(sana_from, '%Y-%m-%d').date()
            queryset = queryset.filter(sana__date__gte=sana_from)
        if sana_to:
            sana_to = datetime.strptime(sana_to, '%Y-%m-%d').date()
            queryset = queryset.filter(sana__date__lte=sana_to)
        
        # Agar hech qanday filtr berilmagan bo'lsa, oxirgi 30 kunlik harakatlar
        if not any([xomashyo_id, harakat_turi, sana_from, sana_to]):
            default_date = datetime.now() - timedelta(days=30)
            queryset = queryset.filter(sana__gte=default_date)
        
        return generate_xomashyo_harakat_pdf(queryset)
    

