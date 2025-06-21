from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from main.models import Ishchi,CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Foydalanuvchi Ishchi bo'lsa
            if hasattr(user, 'ishchi_profile'):
                return redirect('userapp:user_home')
            # Admin yoki superuser
            if user.is_superuser or user.is_staff:
                return redirect('main:home')
            # Aks holda oddiy user
            return redirect('main:home')
        else:
            messages.error(request, 'Login yoki parol noto‘g‘ri')
    return render(request, 'login.html')


def register_page(request):
    ishchilar = Ishchi.objects.all()
    # ...
    return render(request, "register.html", {"ishchilar": ishchilar})

def register_view(request):
    ishchilar = Ishchi.objects.all()
    if request.method == "POST":
        username = request.POST.get("username")
        worker_id = request.POST.get("worker")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Ishchi tanlanganmi va mavjudmi
        try:
            ishchi = Ishchi.objects.get(id=worker_id)
        except (Ishchi.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Ishchini tanlang!")
            return render(request, "register.html", {"ishchilar": ishchilar})

        # Parollar mosligi
        if password1 != password2:
            messages.error(request, "Parollar mos emas!")
            return render(request, "register.html", {"ishchilar": ishchilar})

        # Ishchida user bog'langanmi
        if ishchi.user is not None:
            messages.error(request, "Bu ishchiga boshqa akkaunt biriktirilgan!")
            return render(request, "register.html", {"ishchilar": ishchilar})

        # Login band emasligini tekshirish
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Bunday login allaqachon mavjud!")
            return render(request, "register.html", {"ishchilar": ishchilar})

        # User yaratish va biriktirish
        user = CustomUser.objects.create(
            username=username,
            password=make_password(password1),
        )
        ishchi.user = user
        ishchi.save()

        messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz. Endi tizimga kiring.")
        return redirect("autentific:login_page")

    return render(request, "register.html", {"ishchilar": ishchilar})

@login_required
@login_required
def custom_logout(request):
    """Foydalanuvchini tizimdan chiqarish va xabar bilan login sahifasiga yo'naltirish"""
    logout(request)
    messages.info(request, "Siz tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('autentific:login_page')
