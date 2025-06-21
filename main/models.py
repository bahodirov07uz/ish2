from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.utils.timezone import now
from datetime import date
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from shop.models import Product
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import qrcode
from io import BytesIO
from django.core.files import File

class CustomUser(AbstractUser):
    telefon = models.CharField(max_length=15, blank=True, null=True)
    is_ishchi = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class Category(models.Model):
    nomi = models.CharField(max_length=50)

    def __str__(self):
        return self.nomi

class Oyliklar(models.Model):
    sana = models.DateField(default=now)
    ishchi = models.ForeignKey(
        'Ishchi', on_delete=models.CASCADE, related_name='oyliklar'
    )
    oylik = models.IntegerField(null=True)
    yopilgan = models.BooleanField(default=False)
    ishlari = models.ForeignKey('EskiIsh', on_delete=models.CASCADE, null=True, related_name='oylik_ishlari')

    def __str__(self):
        return f"{self.ishchi.ism} - {self.sana} - {self.oylik}"

class Ishchi(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Asosan CustomUserga ishora qiladi
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ishchi_profile'
    )
    ism = models.CharField(max_length=50)
    familiya = models.CharField(max_length=50)
    maosh = models.IntegerField()
    telefon = models.CharField(max_length=15)  # O'zgartirilgan
    turi = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name='ish_turi')
    is_oylik_open = models.BooleanField(default=True, null=True)
    oldingi_oylik = models.IntegerField(default=0, null=True, blank=True)
    yangi_oylik = models.IntegerField(default=0, null=True)
    oylik_yopilgan_sana = models.DateField(auto_now=True, null=True)
    current_oylik = models.OneToOneField(
        Oyliklar, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_ishchi"
    )
    eski_ishlar = models.ForeignKey('EskiIsh', on_delete=models.CASCADE, related_name='ishchilar', null=True, blank=True)

    def __str__(self):
        return f"{self.ism} {self.familiya}"

    def umumiy_oylik(self):
        umumiy_summa = sum(
            ish.narxi for ish in self.ishlar.filter(sana__month=now().month)
        )
        return umumiy_summa

    @staticmethod
    def ishlar_soni():
        kosib_turi = Category.objects.get(nomi='kosib')
        return Ish.objects.filter(ishchi__turi=kosib_turi).aggregate(umumiy_soni=Sum('soni'))['umumiy_soni'] or 0

class EskiIsh(models.Model):
    ishchi = models.ForeignKey(Ishchi, on_delete=models.CASCADE, null=True)
    mahsulot = models.CharField(max_length=500, null=True)
    sana = models.DateField(null=True)
    narxi = models.IntegerField(null=True)
    soni = models.IntegerField(null=True)
    ishchi_oylik = models.ForeignKey(
        Oyliklar, on_delete=models.CASCADE, null=True, related_name='eski_ishlar'
    )

class Ish(models.Model):
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE)
    soni = models.IntegerField(null=True)
    sana = models.DateField(null=True, auto_now_add=True)
    narxi = models.IntegerField(null=True, blank=True)
    ishchi = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE, null=True, related_name='ishlar'
    )

    def __str__(self):
        return self.mahsulot.nomi

    def save(self, *args, **kwargs):
        if self.ishchi and self.ishchi.turi:
            if self.ishchi.turi.nomi == "kosib":
                self.narxi = self.mahsulot.narx_kosib * int(self.soni)
            elif self.ishchi.turi.nomi == "zakatovka":
                self.narxi = self.mahsulot.narx_zakatovka * int(self.soni)
            elif self.ishchi.turi.nomi == "kroy":
                self.narxi = self.mahsulot.narx_kroy * int(self.soni)
            elif self.ishchi.turi.nomi == "pardozchi":
                self.narxi = self.mahsulot.narx_pardoz * int(self.soni)
        super().save(*args, **kwargs)
        if self.ishchi and self.ishchi.turi and self.ishchi.turi.nomi == "kosib":
            from django.db.models import Sum
            jami = self.__class__.objects.filter(
                mahsulot=self.mahsulot,
                ishchi__turi__nomi="kosib"
            ).aggregate(Sum('soni'))['soni__sum'] or 0
            self.mahsulot.soni = jami
            self.mahsulot.save()

class ChiqimTuri(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Chiqim(models.Model):
    name = models.CharField(max_length=500)
    category = models.ForeignKey(
        ChiqimTuri, related_name='chiqimlar', null=True, blank=True, on_delete=models.CASCADE
    )
    price = models.PositiveIntegerField()
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    @staticmethod
    def sum_prices():
        today = date.today()
        return Chiqim.objects.filter(
            created__year=today.year, created__month=today.month
        ).aggregate(Sum('price'))['price__sum'] or 0

class Xaridor(models.Model):
    name = models.CharField(max_length=500)
    mahsuloti = models.ManyToManyField(Product, blank=True)
    telefon = models.CharField(max_length=100, null=True)
    def __str__(self):
        return self.name

    def umumiy_summa(self):
        return sum(kirim.summa for kirim in self.kirimlar.all())

class Kirim(models.Model):
    xaridor = models.ForeignKey(Xaridor, on_delete=models.CASCADE, related_name='kirimlar')
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    summa = models.PositiveIntegerField()
    sana = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.mahsulot.soni < self.quantity:
                raise ValueError(f"Omborda yetarli {self.mahsulot.nomi} mahsulot yo'q!")
            self.mahsulot.soni -= self.quantity
            self.mahsulot.save()
        self.summa = self.mahsulot.narxi * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.xaridor.name} - {self.mahsulot.nomi} ({self.quantity} dona)"

class Xomashyo(models.Model):
    OLCHOV_BIRLIKLARI = [
        ('kg', 'Kilogramm'),
        ('gr', 'Gramm'),
        ('lt', 'Litr'),
        ('dona', 'Dona'),
        ('dm', 'detsimetr')
    ]
    nomi = models.CharField(max_length=255)
    miqdori = models.DecimalField(max_digits=10, decimal_places=2)
    olchov_birligi = models.CharField(max_length=20, choices=OLCHOV_BIRLIKLARI)
    minimal_miqdor = models.DecimalField(max_digits=10, decimal_places=2)
    narxi = models.DecimalField(max_digits=15, decimal_places=2)
    yetkazib_beruvchi = models.ForeignKey('YetkazibBeruvchi', on_delete=models.SET_NULL, null=True)
    qabul_qilingan_sana = models.DateField(auto_now_add=True)
    amal_qilish_muddati = models.DateField(null=True, blank=True)
    holati = models.CharField(max_length=20, choices=[
        ('active', 'Faol'),
        ('deactive', 'Nofaol'),
        ('expired', 'Muddati otgan')
    ])
    qr_code = models.CharField(max_length=100, blank=True)

    def generate_qr_code(self):
        try:
            qr_info = f"""
            Xomashyo: {self.nomi}
            ID: {self.id}
            Miqdor: {self.miqdori} {self.get_olchov_birligi_display()}
            Qabul qilingan: {self.qabul_qilingan_sana}
            Muddati: {self.amal_qilish_muddati or 'Muddatsiz'}
            """
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_info.strip())
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
            os.makedirs(qr_dir, exist_ok=True)
            filename = f'xomashyo_{self.id}.png'
            filepath = os.path.join(qr_dir, filename)
            img.save(filepath)
            self.qr_code = os.path.join('qr_codes', filename)
            self.save()
            return filepath
        except Exception as e:
            print(f"QR kod yaratishda xatolik: {str(e)}")
            return None

class YetkazibBeruvchi(models.Model):
    nomi = models.CharField(max_length=255)
    telefon = models.CharField(max_length=20)
    manzil = models.TextField()
    inn = models.CharField(max_length=20, blank=True)
    qisqacha_tavsif = models.TextField(blank=True)

class XomashyoHarakat(models.Model):
    HARAKAT_TURLARI = [
        ('kirim', 'Kirim'),
        ('chiqim', 'Chiqim'),
        ('inventarizatsiya', 'Inventarizatsiya'),
        ('qaytarish', 'Qaytarish')
    ]
    xomashyo = models.ForeignKey(Xomashyo, on_delete=models.CASCADE)
    harakat_turi = models.CharField(max_length=20, choices=HARAKAT_TURLARI)
    miqdori = models.DecimalField(max_digits=10, decimal_places=2)
    izoh = models.TextField(blank=True)
    sana = models.DateTimeField(auto_now_add=True)
    narxi = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    yetkazib_beruvchi = models.ForeignKey(YetkazibBeruvchi, on_delete=models.SET_NULL, null=True, blank=True)
    foydalanuvchi = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)  # CustomUser

    def clean(self):
        if self.harakat_turi != 'kirim' and self.miqdori > self.xomashyo.miqdori:
            raise ValidationError("Omborda yetarli xomashyo mavjud emas!")
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.harakat_turi == 'kirim':
            Chiqim.objects.create(
                name=f"{self.xomashyo.nomi} chiqimi ({self.miqdori} dona)",
                category=None,
                price=int(self.narxi) if self.narxi else 0,
                created=self.sana.date() if self.sana else now().date()
            )

@receiver(post_save, sender=XomashyoHarakat)
def update_xomashyo_miqdori(sender, instance, **kwargs):
    if instance.harakat_turi == 'kirim':
        instance.xomashyo.miqdori += instance.miqdori
    else:
        instance.xomashyo.miqdori -= instance.miqdori
    instance.xomashyo.save()
    
class IshRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ish_requests', null=True)
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE)
    soni = models.IntegerField(null=True)
    sana = models.DateField(null=True, blank=True)
    ishchi = models.ForeignKey(
        'Ishchi', on_delete=models.CASCADE, null=True,blank=True, related_name='ish_requests'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.mahsulot.nomi} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.sana:
            self.sana = now().date()

        if not self.ishchi and self.user and hasattr(self.user, 'ishchi_profile'):
            self.ishchi = self.user.ishchi_profile

        creating = self._state.adding

        super().save(*args, **kwargs)

        if creating and self.status == 'approved':
            Ish.objects.create(
                mahsulot=self.mahsulot,
                soni=self.soni,
                sana=self.sana,
                ishchi=self.ishchi,
            )

    class Meta:
        permissions = [
            ('can_approve_ishrequest', 'Can approve work requests'),
        ]