from django.db import models

# Hotel model (represents a restaurant/hotel)
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models

class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    qr_code = models.CharField(max_length=20, unique=True)
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    hotel_image = models.ImageField(upload_to='hotel_images/', blank=True, null=True)  # <-- Add this line

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Create QR code image pointing to menu URL
        url = f"http://127.0.0.1:8000/menu/{self.qr_code}/"
        qr = qrcode.make(url)
        stream = BytesIO()
        qr.save(stream, format='PNG')
        self.qr_image.save(f'{self.qr_code}.png', File(stream), save=False)
        super().save(*args, **kwargs)


# Category model (e.g. Starters, Main Course, Drinks)
class Category(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.hotel.name})"

# Menu Item model (individual food items)
class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"
