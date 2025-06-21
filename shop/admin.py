from django.contrib import admin
# Register your models here.
from django.contrib import admin
from .models import *
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user",  "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "product__name")
    actions = ["mark_as_processing", "mark_as_delivered", "mark_as_cancelled"]

    def mark_as_processing(self, request, queryset):
        queryset.update(status="processing")

    def mark_as_delivered(self, request, queryset):
        queryset.update(status="delivered")

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status="cancelled")

    mark_as_processing.short_description = "Buyurtmalarni 'Yetkazib berilyapti' qilish"
    mark_as_delivered.short_description = "Buyurtmalarni 'Yetkazib berildi' qilish"
    mark_as_cancelled.short_description = "Buyurtmalarni 'Bekor qilindi' qilish"
    
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('product', 'rating')

admin.site.register(Delivery)
admin.site.register(Category)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(Viloyat)







class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0  # Yangi mahsulot qo‘shilganda yangi satr chiqarmaydi

class ProductAdmin(admin.ModelAdmin):
    list_display = ("nomi", "category", "narxi", "soni")
    search_fields = ("nomi", "category__name")
    inlines = [ProductVariantInline]

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant)