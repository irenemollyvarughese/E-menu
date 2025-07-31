from django.contrib import admin
from .models import *

# Show Category inline inside Hotel admin
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1

# Show MenuItems inline inside Category admin
class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1

from django.utils.html import mark_safe

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'qr_code', 'qr_preview']

    def qr_preview(self, obj):
        if obj.qr_image:
            return mark_safe(f'<img src="{obj.qr_image.url}" width="100" />')
        return "(No QR yet)"
    qr_preview.short_description = 'QR Code'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel']
    inlines = [MenuItemInline]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'available']
    list_filter = ['category', 'available']
    search_fields = ['name', 'description']




# new adding



# ---------------- Order & OrderItem Setup ----------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_item', 'quantity', 'price']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'hotel', 'guest_count', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['hotel', 'payment_method', 'created_at']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    search_fields = ['id', 'hotel__name']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'price']
    list_filter = ['menu_item']
    search_fields = ['order__id', 'menu_item__name']