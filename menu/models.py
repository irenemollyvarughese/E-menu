from django.db import models
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.utils.text import slugify
import qrcode

# -----------------------------
# Hotel (unchanged, generates a "hotel landing" QR)
# -----------------------------


class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    qr_code = models.CharField(max_length=20, unique=True)
   
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    
    password = models.CharField(max_length=128, null=True, blank=True)  # store raw password (not secure, better to hash)
    phone = models.CharField(max_length=15,null=True, blank=True)
   
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    wifi_name = models.CharField(max_length=100, blank=True, null=True)
    wifi_password = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)


    hotel_image = models.ImageField(upload_to='hotel_images/', blank=True, null=True)



    def __str__(self):
        return self.name



# -----------------------------
# Category
# -----------------------------
class Category(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.hotel.name})"


# -----------------------------
# Tag
# -----------------------------
class Tag(models.Model):
    name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return f"{self.name} {self.emoji}".strip()


# -----------------------------
# MenuItem
# -----------------------------
TONE_CHOICES = [
    ('appetizing', 'Appetizing'),
    ('formal', 'Formal'),
    ('casual', 'Casual'),
    ('humorous', 'Humorous'),
    ('poetic', 'Poetic'),
]

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True)
    available = models.BooleanField(default=True)
    description_tone = models.CharField(
        max_length=20,
        choices=TONE_CHOICES,
        default='appetizing',
        help_text=("Tone style for AI-generated description")
    )
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


# -----------------------------
# DiningTable (NEW)
# -----------------------------
class DiningTable(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='tables')
    number = models.CharField(max_length=10)  # "1", "A1", "VIP-2", etc.
    table_code = models.SlugField(max_length=40, unique=True, blank=True)  # globally unique code
    qr_image = models.ImageField(upload_to='qr_codes/tables/', blank=True, null=True)
    seats = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hotel', 'number'], name='unique_table_per_hotel'),
        ]
        ordering = ['hotel_id', 'number']

    def __str__(self):
        return f"Table {self.number} - {self.hotel.name}"

    def _base_url(self):
        return getattr(settings, "PUBLIC_BASE_URL", "http://127.0.0.1:8000")

    def _menu_url(self):
        # URL encodes hotel + table so scanning knows the table immediately
        return f"{self._base_url()}/menu/{self.hotel.qr_code}/{self.table_code}/"

    def save(self, *args, **kwargs):
        # Generate a stable unique code if missing: HOTELQR-table-number-slug
        if not self.table_code:
            num_slug = slugify(str(self.number))
            self.table_code = f"{self.hotel.qr_code}-{num_slug}"

        super().save(*args, **kwargs)

        # Generate the table QR if missing
        if not self.qr_image:
            img = qrcode.make(self._menu_url())
            stream = BytesIO()
            img.save(stream, format='PNG')
            self.qr_image.save(f'{self.table_code}.png', File(stream), save=False)
            super().save(update_fields=['qr_image'])


# -----------------------------
# Order + OrderItem
# -----------------------------
STATUS_CHOICES = [
    ('New', 'New'),
    ('Preparing', 'Preparing'),
    ('Ready', 'Ready'),
    ('Served', 'Served'),
]

class Order(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    table = models.ForeignKey(DiningTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_count = models.PositiveIntegerField(default=1)
    payment_method = models.CharField(max_length=10, choices=[('COD', 'Cash'), ('ONLINE', 'Online')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        table_txt = f"Table {self.table.number}" if self.table else "No table"
        return f"Order #{self.id} - {table_txt} - {self.status}"

    @property
    def status_path(self):
        flow = [choice[0] for choice in STATUS_CHOICES]
        if self.status in flow:
            idx = flow.index(self.status)
            return flow[:idx]
        return []


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)