from django.shortcuts import render,redirect

from main.models import Oyliklar 
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from main.models import Ish, IshRequest, Ishchi, EskiIsh
from calendar import monthrange
from django.utils.timezone import now
from django.http import JsonResponse
from datetime import timedelta, date
def user_home(request):
    # Foydalanuvchi tizimga kirmagan bo'lsa, login sahifasiga yo'naltiramiz
    if not request.user.is_authenticated:
        return redirect('autentific:login_page')

    now = timezone.now()
    current_month = now.month
    current_year = now.year
    last_month = (now.replace(day=1) - timedelta(days=1)).month
    last_month_year = (now.replace(day=1) - timedelta(days=1)).year

    # Foydalanuvchi ishchi bo'lsa, unga tegishli ma'lumotlarni olamiz
    if hasattr(request.user, 'ishchi_profile'):
        ishchi = request.user.ishchi_profile
        
        # 1. Bajarilgan ishlar (hozirgi oy) - Ish modelidagi soni yig'indisi
        completed_works = Ish.objects.filter(
            sana__month=current_month,
            sana__year=current_year,
            ishchi=ishchi
        ).aggregate(total=Sum('soni'))['total'] or 0

        # Bajarilgan ishlar (o'tgan oy) - EskiIsh modelidagi soni yig'indisi
        last_month_completed = EskiIsh.objects.filter(
            sana__month=last_month,
            sana__year=last_month_year,
            ishchi=ishchi
        ).aggregate(total=Sum('soni'))['total'] or 0

        # 2. Jarayondagi ishlar (pending requests) - soni yig'indisi
        pending_works = IshRequest.objects.filter(
            status='pending',
            user=request.user
        ).aggregate(total=Sum('soni'))['total'] or 0

        # 3. Ish haqi - faqat shu ishchining oyligi
        current_salary = ishchi.umumiy_oylik() or 0

        # O'tgan oy ish haqi (faqat shu ishchi uchun)
        last_month_salary = Oyliklar.objects.filter(
            sana__month=last_month,
            sana__year=last_month_year,
            ishchi=ishchi
        ).aggregate(total_salary=Sum('oylik'))['total_salary'] or 0

    else:
        # Admin yoki boshqa foydalanuvchi uchun barcha ma'lumotlarni ko'rsatish
        completed_works = Ish.objects.filter(
            sana__month=current_month,
            sana__year=current_year
        ).aggregate(total=Sum('soni'))['total'] or 0

        last_month_completed = EskiIsh.objects.filter(
            sana__month=last_month,
            sana__year=last_month_year
        ).aggregate(total=Sum('soni'))['total'] or 0

        pending_works = IshRequest.objects.filter(
            status='pending'
        ).aggregate(total=Sum('soni'))['total'] or 0

        current_salary = sum(
            (ishchi.umumiy_oylik() or 0) for ishchi in Ishchi.objects.all()
        )

        last_month_salary = Oyliklar.objects.filter(
            sana__month=last_month,
            sana__year=last_month_year
        ).aggregate(total_salary=Sum('oylik'))['total_salary'] or 0

    # Foiz o'zgarishi hisoblari
    if last_month_completed > 0:
        completed_change_percent = ((completed_works - last_month_completed) / last_month_completed) * 100
    else:
        completed_change_percent = 100 if completed_works > 0 else 0

    if last_month_salary > 0:
        salary_change_percent = ((current_salary - last_month_salary) / last_month_salary) * 100
    else:
        salary_change_percent = 100 if current_salary > 0 else 0

    # Faqat foydalanuvchiga tegishli oxirgi ishlar va so'rovlar
    if hasattr(request.user, 'ishchi_profile'):
        recent_works = Ish.objects.filter(
            ishchi=request.user.ishchi_profile
        ).order_by('-sana')[:5]
        
        pending_requests = IshRequest.objects.filter(
            user=request.user,
            status='pending'
        ).order_by('-created_at')[:5]
    else:
        recent_works = Ish.objects.order_by('-sana')[:5]
        pending_requests = IshRequest.objects.filter(
            status='pending'
        ).order_by('-created_at')[:5]

    context = {
        'stats': [
            {
                'title': 'Bajarilgan ishlar',
                'value': completed_works,
                'change': round(completed_change_percent, 2),
                'is_positive': completed_change_percent >= 0,
                'icon': 'check-circle',
                'color': 'success'
            },
            {
                'title': 'Jarayondagi ishlar',
                'value': pending_works,
                'change': None,
                'is_positive': None,
                'icon': 'clock',
                'color': 'warning'
            },
            {
                'title': 'Ish haqi',
                'value': f"{current_salary:,} so'm",
                'change': round(salary_change_percent, 2),
                'is_positive': salary_change_percent >= 0,
                'icon': 'currency-dollar',
                'color': 'primary'
            },
        ],
        'recent_works': recent_works,
        'pending_requests': pending_requests
    }

    return render(request, 'user/user_home.html', context)

def ishchi_chart_page(request):
    return render(request, 'user/statistics.html')

def get_ish_chart_data(request):
    user = request.user

    # Foydalanuvchining ishchi profili borligini tekshiramiz
    if not hasattr(user, 'ishchi_profile'):
        return JsonResponse({'error': 'Ishchi profili topilmadi'}, status=400)

    ishchi = user.ishchi_profile
    today = now().date()

    current_month_start = today.replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    # Joriy oydagi ishlar (Ish modeli)
    current_month_ish = Ish.objects.filter(
        ishchi=ishchi,
        sana__year=today.year,
        sana__month=today.month
    ).aggregate(
        jami_narxi=Sum('narxi'),
        jami_soni=Sum('soni')
    )

    # O‘tgan oydagi ishlar (EskiIsh modeli)
    last_month_ish = EskiIsh.objects.filter(
        ishchi=ishchi,
        sana__year=last_month_start.year,
        sana__month=last_month_start.month
    ).aggregate(
        jami_narxi=Sum('narxi'),
        jami_soni=Sum('soni')
    )

    data = {
        'labels': ['O‘tgan oy', 'Joriy oy'],
        'jami_narxi': [
            last_month_ish['jami_narxi'] or 0,
            current_month_ish['jami_narxi'] or 0
        ],
        'jami_soni': [
            last_month_ish['jami_soni'] or 0,
            current_month_ish['jami_soni'] or 0
        ]
    }

    return JsonResponse(data)