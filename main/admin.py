from django.contrib import admin
from .models import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin

class IshAdmin(admin.ModelAdmin):
    list_display = ['ishchi', 'mahsulot', 'soni', 'narxi', 'sana']



@admin.register(Ishchi)
class IshchiAdmin(admin.ModelAdmin):
    list_display = ('ism', 'familiya', 'telefon', 'turi', 'oldingi_oylik', 'yangi_oylik', 'oylik_yopilgan_sana')
    list_filter = ('turi', 'oylik_yopilgan_sana')
    search_fields = ('ism', 'familiya', 'telefon')

@admin.register(Chiqim)
class IshchiAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created','category')
    search_fields = ('name', 'price', 'created','category')
    # list_editable = ['is_oylik_open']



@admin.register(EskiIsh)
class EskiIshAdmin(admin.ModelAdmin):
    list_display = ('ishchi','ishchi_oylik','soni')
        # list_filter = ('turi', 'oylik_yopilgan_sana')
        # search_fields = ('ism', 'familiya', 'telefon')

@admin.register(Ish)
class IshAdmin(admin.ModelAdmin):
    list_display = ('mahsulot','ishchi','soni','sana','narxi')
        # list_filter = ('turi', 'oylik_yopilgan_sana')
        # search_fields = ('ism', 'familiya', 'telefon')


@admin.register(Xaridor)
class XaridorAdmin(admin.ModelAdmin):
    # list_display = ('name', 'mahsuloti')
    readonly_fields = ('umumiy_summa',)

@admin.register(Kirim)
class KirimAdmin(admin.ModelAdmin):
    list_display = ('mahsulot', 'xaridor', 'quantity', 'summa', 'sana')
    list_filter = ('sana', 'mahsulot')  # Filtr mahsulot va sanaga ko'ra
    search_fields = ('mahsulot__nomi', 'xaridor__ism')  # Qidiruv maydoni
    date_hierarchy = 'sana'  # Sanalar bo'yicha qidiruv

    def mahsulot_nomi(self, obj):
        """Mahsulot nomini qaytarish."""
        return obj.mahsulot.nomi
    mahsulot_nomi.short_description = 'Mahsulot Nomi'

    def xaridor_ismi(self, obj):
        """Xaridor ismini qaytarish."""
        return obj.xaridor.ism
    xaridor_ismi.short_description = 'Xaridor Ismi'

    def summa(self, obj):
        """Umumiy summani qaytarish."""
        return obj.quantity * obj.mahsulot.narxi
    summa.short_description = 'Umumiy Narx'



class XomashyoHarakatInline(admin.TabularInline):
    """Xomashyo uchun harakatlar inline ko'rinishi"""
    model = XomashyoHarakat
    extra = 0
    readonly_fields = ('sana', 'foydalanuvchi')
    fields = ('harakat_turi', 'miqdori', 'sana', 'foydalanuvchi', 'izoh')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Xomashyo)
class XomashyoAdmin(admin.ModelAdmin):
    list_display = ('nomi', 'miqdori', 'olchov_birligi', 'minimal_miqdor', 'narxi', 'yetkazib_beruvchi', 'holati')
    list_filter = ('olchov_birligi', 'holati', 'yetkazib_beruvchi')
    search_fields = ('nomi', 'qr_code')
    readonly_fields = ('qr_code_preview',)
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('nomi', 'miqdori', 'olchov_birligi', 'minimal_miqdor', 'narxi')
        }),
        ('Yetkazib beruvchi', {
            'fields': ('yetkazib_beruvchi', 'amal_qilish_muddati')
        }),
        ('Holati', {
            'fields': ('holati', 'qr_code', 'qr_code_preview')
        }),
    )
    inlines = [XomashyoHarakatInline]
    actions = ['generate_qr_codes', 'check_expiry']

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return f'<img src="/media/{obj.qr_code}" width="100" height="100" />'
        return "QR kod mavjud emas"
    qr_code_preview.short_description = 'QR kod'
    qr_code_preview.allow_tags = True

    def generate_qr_codes(self, request, queryset):
        for xomashyo in queryset:
            xomashyo.generate_qr_code()
        self.message_user(request, f"{queryset.count()} ta xomashyo uchun QR kodlar yaratildi")
    generate_qr_codes.short_description = "Tanlanganlar uchun QR kod generatsiya qilish"

    def check_expiry(self, request, queryset):
        from datetime import date
        today = date.today()
        expired = queryset.filter(amal_qilish_muddati__lt=today)
        for xomashyo in expired:
            xomashyo.holati = 'expired'
            xomashyo.save()
        self.message_user(request, f"{expired.count()} ta xomashyo muddati o'tgan deb belgilandi")
    check_expiry.short_description = "Muddati o'tgan xomashyolarni belgilash"

@admin.register(YetkazibBeruvchi)
class YetkazibBeruvchiAdmin(admin.ModelAdmin):
    list_display = ('nomi', 'telefon', 'inn', 'manzil')
    search_fields = ('nomi', 'inn', 'telefon')
    list_filter = ('inn',)
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('nomi', 'telefon', 'inn')
        }),
        ('Qo\'shimcha', {
            'fields': ('manzil', 'qisqacha_tavsif')
        }),
    )

@admin.register(XomashyoHarakat)
class XomashyoHarakatAdmin(admin.ModelAdmin):
    list_display = ('display_xomashyo', 'harakat_turi', 'miqdori_with_unit', 'sana', 'foydalanuvchi')
    list_filter = ('harakat_turi', 'sana')
    search_fields = ('xomashyo__nomi', 'izoh')
    readonly_fields = ('sana', 'foydalanuvchi')
    date_hierarchy = 'sana'

    @admin.display(description='Xomashyo', ordering='xomashyo__nomi')
    def display_xomashyo(self, obj):
        return f"{obj.xomashyo.nomi} ({obj.xomashyo.olchov_birligi})"

    @admin.display(description='Miqdori')
    def miqdori_with_unit(self, obj):
        return f"{obj.miqdori} {obj.xomashyo.olchov_birligi}"

    @admin.display(description='Foydalanuvchi')
    def user_info(self, obj):
        if obj.foydalanuvchi:
            return f"{obj.foydalanuvchi.get_full_name() or obj.foydalanuvchi.username}"
        return "-"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('xomashyo', 'foydalanuvchi')
    fieldsets = (
        ('Harakat ma\'lumotlari', {
            'fields': ('xomashyo', 'harakat_turi', 'miqdori')
        }),
        ('Qo\'shimcha', {
            'fields': ('sana', 'foydalanuvchi', 'izoh')
        }),
    )

    def save_model(self, request, obj, form, change):
        """Harakat qo'shishda foydalanuvchini avtomatik belgilash"""
        if not obj.pk:
            obj.foydalanuvchi = request.user
        super().save_model(request, obj, form, change)

@admin.register(Oyliklar)
class OyliklarAdmin(admin.ModelAdmin):
    list_display = ('id', 'sana', 'ishchi', 'oylik', 'yopilgan')  # admin ro'yxatda ko'rinadiganlar
    list_filter = ('yopilgan', 'sana', 'ishchi')  # yon panelda filter
    search_fields = ('ishchi__ism', 'ishchi__familya')  # qidiruv
    # autocomplete_fields = ['ishchi', 'ishlari']  # select qidiruv
    date_hierarchy = 'sana'  # yuqorida sana bo‘yicha navigatsiya

    # O‘zgartirishni oldini olish (agar yopilgan bo‘lsa)
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.yopilgan:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

admin.site.register(Category)


@admin.register(IshRequest)
class IshRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_info', 'mahsulot_info', 'soni', 'sana', 'ishchi_info', 'status', 'status_display', 'action_buttons')
    list_filter = ('status', 'sana', 'ishchi')
    search_fields = ('user__username', 'mahsulot__nomi', 'ishchi__ism')
    list_editable = ('status',)
    date_hierarchy = 'sana'
    actions = ['approve_selected', 'reject_selected']
    
    fieldsets = (
        (_("Asosiy ma'lumotlar"), {
            'fields': ('user', 'mahsulot', 'soni', 'sana', 'ishchi', 'notes')
        }),
        (_("Status"), {
            'fields': ('status',)
        }),
    )
    
    def user_info(self, obj):
        return f"{obj.user.username}"
    user_info.short_description = _("Foydalanuvchi")
    
    def mahsulot_info(self, obj):
        return obj.mahsulot.nomi
    mahsulot_info.short_description = _("Mahsulot")
    
    def ishchi_info(self, obj):
        return f"{obj.ishchi.ism} {obj.ishchi.familiya}"
    ishchi_info.short_description = _("Ishchi")
    
    def status_display(self, obj):
        status_map = {
            'pending': _("Kutilmoqda"),
            'approved': _("Tasdiqlandi"),
            'rejected': _("Rad etildi"),
        }
        return status_map.get(obj.status, obj.status)
    status_display.short_description = _("Holati (ko'rinish)")
    
    def action_buttons(self, obj):
        from django.utils.html import format_html
        if obj.status == 'pending':
            return format_html(
                '<div class="action-buttons-container">'
                '<a class="button approve-button" href="{}">Tasdiqlash</a>'
                '<a class="button reject-button" href="{}">Rad etish</a>'
                '</div>',
                f"{obj.id}/approve/",
                f"{obj.id}/reject/"
            )
        return ""
    action_buttons.short_description = _("Amallar")
    action_buttons.allow_tags = True
    
    def approve_selected(self, request, queryset):
        queryset.update(status='approved')
        for obj in queryset:
            if not hasattr(obj, 'created_ish'):
                Ish.objects.create(
                    mahsulot=obj.mahsulot,
                    soni=obj.soni,
                    sana=obj.sana,
                    ishchi=obj.ishchi,
                )
        self.message_user(request, _("Tanlangan so'rovlar tasdiqlandi"))
    approve_selected.short_description = _("Tanlanganlarni tasdiqlash")
    
    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, _("Tanlangan so'rovlar rad etildi"))
    reject_selected.short_description = _("Tanlanganlarni rad etish")
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.approve_request), name='ishrequest-approve'),
            path('<path:object_id>/reject/', self.admin_site.admin_view(self.reject_request), name='ishrequest-reject'),
        ]
        return custom_urls + urls
    
    def approve_request(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        from .models import Ish
        
        obj = self.get_object(request, object_id)
        obj.status = 'approved'
        obj.save()
        
        # Ish yaratish
        Ish.objects.create(
            mahsulot=obj.mahsulot,
            soni=obj.soni,
            sana=obj.sana,
            ishchi=obj.ishchi,
        )
        
        messages.success(request, _("So'rov muvaffaqiyatli tasdiqlandi va ish yaratildi!"))
        return redirect('admin:main_ishrequest_changelist')

    
    def reject_request(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        obj = self.get_object(request, object_id)
        obj.status = 'rejected'
        obj.save()
        messages.warning(request, _("So'rov rad etildi!"))
        return redirect('admin:main_ishrequest_changelist')
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Agar user ishchi bo'lsa (user.ishchi_profili bor bo'lsa)
        if hasattr(request.user, 'ishchi_profili'):
            form.base_fields['ishchi'].initial = request.user.ishchi_profili
            form.base_fields['ishchi'].disabled = True
        return form
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Agar user ishchi bo'lsa, faqat o'ziga tegishli so'rovlarni ko'rsatish
        if hasattr(request.user, 'ishchi_profili'):
            return qs.filter(user=request.user)
        return qs
 
 
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    fieldsets = UserAdmin.fieldsets + (
        # Qo‘shimcha maydonlaringiz bo‘lsa shu yerga yozing
        ('Qo‘shimcha ma’lumotlar', {'fields': ('is_ishchi', )}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('is_ishchi', )}),
    )
