from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Hotel, Category, MenuItem, Tag,
    Order, OrderItem, DiningTable
)

# ---------------- Inlines ----------------

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


class DiningTableInline(admin.TabularInline):
    model = DiningTable
    extra = 1
    fields = ('number', 'seats', 'is_active', 'qr_preview')
    readonly_fields = ('qr_preview',)

    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" width="64" height="64" style="object-fit:cover;border-radius:8px;border:1px solid #eee;" />',
                obj.qr_image.url
            )
        return '-'
    qr_preview.short_description = "QR"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_item', 'quantity', 'price']
    can_delete = False


# ---------------- Admin classes ----------------


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "qr_code",
        "phone",
        "password",
        "username",
        "start_time",
        "end_time",
        "preview_image",
    )
    list_filter = ("start_time", "end_time",)
    search_fields = ("name", "location","phone", "username", "qr_code")
    ordering = ("name",)

    # show image preview in admin list
    def preview_image(self, obj):
        if obj.hotel_image:
            return format_html('<img src="{}" width="60" height="40" style="object-fit:cover;"/>', obj.hotel_image.url)
        return "No Image"
    preview_image.short_description = "Hotel Image"



@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'number', 'seats', 'is_active', 'qr_preview')
    list_filter = ('hotel', 'is_active')
    search_fields = ('number', 'table_code', 'hotel__name')
    readonly_fields = ('qr_preview', 'table_code', 'qr_image')
    actions = ['regenerate_qr']

    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover;border-radius:8px;border:1px solid #eee;" />',
                obj.qr_image.url
            )
        return '-'
    qr_preview.short_description = "QR"

    @admin.action(description="Regenerate QR for selected tables")
    def regenerate_qr(self, request, queryset):
        count = 0
        for obj in queryset:
            # Delete existing QR so model.save() re-creates it
            if obj.qr_image:
                obj.qr_image.delete(save=False)
            obj.qr_image = None
            obj.save()
            count += 1
        self.message_user(request, f"Regenerated QR for {count} table(s).")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel']
    list_filter = ['hotel']
    search_fields = ['name', 'hotel__name']
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'available', 'description_tone']
    list_filter = ['available', 'category__hotel', 'category', 'description_tone']
    search_fields = ['name', 'description']
    autocomplete_fields = ('category',)
    filter_horizontal = ("tags",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "emoji")
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'hotel', 'table_display', 'status', 'guest_count',
                    'payment_method', 'total_amount', 'created_at']
    list_filter = ['hotel', 'status', 'payment_method', 'created_at']
    date_hierarchy = 'created_at'
    search_fields = ['id', 'hotel__name', 'table__number']
    inlines = [OrderItemInline]

    def table_display(self, obj):
        return obj.table.number if getattr(obj, 'table', None) else '—'
    table_display.short_description = 'Table'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'price']
    list_filter = ['menu_item']
    search_fields = ['order__id', 'menu_item__name']