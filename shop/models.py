from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, timedelta
from django.db.models import Sum,Avg
from datetime import date

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('bestseller', 'Bestseller'),
        ('sale', 'Sale'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", null=True)
    nomi = models.CharField(max_length=255)
    # slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    narxi = models.DecimalField(max_digits=10, decimal_places=2)
    soni = models.PositiveIntegerField()  # Omborda qancha bor
    image = models.ImageField(upload_to="products/")
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="tags")
    narx_kosib = models.IntegerField(default=0)
    narx_zakatovka = models.IntegerField(default=0)
    narx_kroy = models.IntegerField(default=0)
    narx_pardoz = models.IntegerField(default=0)

    def update_total_quantity(self):
        """Mahsulotning umumiy miqdorini variantlar miqdorlari yig‘indisiga moslab yangilash."""
        self.soni = self.variants.aggregate(total=models.Sum('stock'))['total'] or 0
        self.save()
    def is_new(self):
        """Mahsulot faqat 7 kun davomida 'NEW' bo‘lishi mumkin"""
        return (now() - self.created_at).days <= 7

    def is_bestseller(self):
        """Agar mahsulot so‘nggi 30 kunda eng ko‘p sotilgan bo‘lsa, bestseller"""
        from shop.models import OrderItem  
        last_30_days = now() - timedelta(days=30)

        total_sold = OrderItem.objects.filter(
            product=self,
            order__created_at__gte=last_30_days
        ).aggregate(total=Sum('quantity'))['total'] or 0

        return total_sold 

    @property
    def total_stock(self):
        """Umumiy mavjud mahsulot miqdorini qaytarish"""
        return sum(variant.stock for variant in self.variants.all())

    def __str__(self):
        return self.nomi
    @staticmethod    
    def get_avg_rating(product_id):
        reting = Comment.objects.filter(product_id=product_id).aggregate(Avg('rating'))['rating__avg'] or 0
        return int(reting)

    def sales(self):
        sales = OrderItem.objects.filter(product=self)
        
        return sales.count()
    def get_price_for_category(self, category_name):
        if category_name == "kosib":
            return self.narx_kosib
        elif category_name == "zakatovka":
            return self.narx_zakatovka
        elif category_name == "kroy":
            return self.narx_kroy
        elif category_name == "pardoz":
            return self.narx_pardoz
              
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10,null=True)  
    color = models.CharField(max_length=50,null=True)  
    stock = models.PositiveIntegerField(default=0,null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    image = models.ImageField(upload_to='product/',null=True)


    def clean(self):
        """Variant miqdorini tekshirish."""
        if self.stock > self.product.soni:
            raise ValidationError(
                f"Variant miqdori ({self.stock}) mahsulotning umumiy miqdoridan ({self.product.update_total_quantity}) oshib ketdi."
            )



    def __str__(self):
        return f"{self.product.nomi} - {self.size} - {self.color}"



    def delete(self, *args, **kwargs):
        """Variant o'chirilganda mahsulotning umumiy miqdorini yangilash."""
        super().delete(*args, **kwargs)
        self.product.update_total_quantity()
    
class Order(models.Model):
    STATUS_CHOICES = [
        ("Kutilmoqda", "⏳ Kutilmoqda"),
        ("Yetkazib berilyapti", "🚚 Yetkazib berilyapti"),
        ("Yetkazib berildi", "✅ Yetkazib berildi"),
        ("Bekor qilindi", "❌ Bekor qilindi"),
    ]
    user = models.ForeignKey('main.CustomUser', on_delete=models.CASCADE, null=True, blank=True)  # ✅ null=True bo‘lishi kerak
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.ForeignKey('Delivery', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Kutilmoqda"
    )

    def can_be_cancelled(self):
        """ Buyurtma 'processing' yoki 'delivered' bo‘lsa, bekor qilib bo‘lmaydi """
        return self.status == "Kutilmoqda"

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,related_name='item_count')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_count')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='orders/', blank=True, null=True)

    # def save(self, *args, **kwargs):
        # variant = self.product.variants.first()

        # if not variant:
        #     raise ValueError(f"{self.product.name} uchun variant mavjud emas!")

        # if variant.stock >= self.quantity:
        #     variant.stock -= self.quantity
        #     variant.save()
        # else:
        #     raise ValueError("Yetarlicha mahsulot mavjud emas!")
    def __str__(self):
        return f"{self.quantity} x {self.product.nomi}"

    def total_narx(self):
        return self.product.narxi*self.quantity

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=50, choices=[("card", "Card"), ("paypal", "PayPal"), ("cash", "Cash on Delivery")]
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)  # To‘langan yoki yo‘qligini belgilaydi
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.id}"

class Viloyat(models.Model):
    name = models.CharField(max_length=100, null=True,blank=True)

    def __str__(self):
        return self.name
    
class Delivery(models.Model):
    viloyat = models.ForeignKey(Viloyat, null=True, blank=True, related_name='delivery',on_delete=models.CASCADE)
    addres = models.CharField(max_length=200)
    postcode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=True)
    user = models.ForeignKey('main.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.viloyat.name} - {self.postcode}"
    


    
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey('main.CustomUser', on_delete=models.CASCADE)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # Bir user bir mahsulotga faqat bitta baho bera oladi

    def __str__(self):
        return f"{self.product.nomi} - {self.rating}⭐ by {self.user.username}"

class Comment(models.Model):
    user = models.ForeignKey('main.CustomUser', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.nomi}"
