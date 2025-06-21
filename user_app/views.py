from django.shortcuts import render

from main.models import Oyliklar 
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from main.models import Ish, IshRequest, Ishchi, EskiIsh

def user_home(request):
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    last_month = (now.replace(day=1) - timedelta(days=1)).month
    last_month_year = (now.replace(day=1) - timedelta(days=1)).year

    # 1. Bajarilgan ishlar (hozirgi oy) - Ish modelidagi soni yig'indisi
    completed_works = Ish.objects.filter(
        sana__month=current_month,
        sana__year=current_year
    ).aggregate(total=Sum('soni'))['total'] or 0

    # Bajarilgan ishlar (o'tgan oy) - EskiIsh modelidagi soni yig'indisi
    last_month_completed = EskiIsh.objects.filter(
        sana__month=last_month,
        sana__year=last_month_year
    ).aggregate(total=Sum('soni'))['total'] or 0

    # Foiz o'zgarishi
    if last_month_completed > 0:
        completed_change_percent = ((completed_works - last_month_completed) / last_month_completed) * 100
    else:
        completed_change_percent = 100 if completed_works > 0 else 0

    # 2. Jarayondagi ishlar (pending requests) - soni yig'indisi
    pending_works = IshRequest.objects.filter(status='pending').aggregate(
        total=Sum('soni')
    )['total'] or 0

    # 3. Ish haqi - Ishchi modelidagi umumiy_oylik() metodi yordamida
    current_salary = 0
    for ishchi in Ishchi.objects.all():
        current_salary += ishchi.umumiy_oylik() or 0

    # O'tgan oy ish haqi (Oyliklar modelidan)
    last_month_salary = Oyliklar.objects.filter(
        sana__month=last_month,
        sana__year=last_month_year
    ).aggregate(
        total_salary=Sum('oylik')
    )['total_salary'] or 0

    # Foiz o'zgarishi
    if last_month_salary > 0:
        salary_change_percent = ((current_salary - last_month_salary) / last_month_salary) * 100
    else:
        salary_change_percent = 100 if current_salary > 0 else 0

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
        'recent_works': Ish.objects.order_by('-sana')[:5],
        'pending_requests': IshRequest.objects.filter(status='pending').order_by('-created_at')[:5]
    }

    return render(request, 'user/user_home.html', context)
