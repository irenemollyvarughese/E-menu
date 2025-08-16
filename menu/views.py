from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import json
import requests
import os

from .models import (
    Hotel, Category, Tag, MenuItem,
    DiningTable, Order, OrderItem
)
from .forms import MenuItemForm, CategoryForm


# -----------------------------
# MOBILE LOGIN / OTP
# -----------------------------

def mobile_login(request, qr_code, table_code=None):
    hotel = get_object_or_404(Hotel, qr_code=qr_code)
    table = None
    if table_code:
        table = get_object_or_404(DiningTable, hotel=hotel, table_code=table_code)

    if request.method == 'POST':
        phone = (request.POST.get('phone') or '').strip()
        if not phone:
            messages.error(request, 'Please enter a valid phone number.')
            return render(request, 'menu/mobile_login.html', {
                'qr_code': qr_code, 'hotel': hotel, 'table': table, 'table_code': table_code
            })

        # TODO: send a real OTP via your provider
        request.session['otp_phone'] = phone
        request.session['otp_code'] = '1234'

        if table:
            request.session['table_id'] = table.id
            return redirect('otp_verify_table', qr_code=qr_code, table_code=table_code)
        return redirect('otp_verify', qr_code=qr_code)

    return render(request, 'menu/mobile_login.html', {
        'qr_code': qr_code,
        'hotel': hotel,
        'table': table,
        'table_code': table_code
    })


def otp_verify(request, qr_code, table_code=None):
    hotel = get_object_or_404(Hotel, qr_code=qr_code)
    table = None
    if table_code:
        table = get_object_or_404(DiningTable, hotel=hotel, table_code=table_code)

    # Optional: resend support (?resend=1)
    if request.method == 'GET' and request.GET.get('resend'):
        phone = request.session.get('otp_phone')
        if phone:
            # TODO: actually resend OTP via your provider
            messages.success(request, 'OTP resent.')
        return render(request, 'menu/otp_verify.html', {
            'qr_code': qr_code, 'hotel': hotel, 'table': table, 'table_code': table_code
        })

    if request.method == 'POST':
        entered_otp = (request.POST.get('otp') or '').strip()
        if entered_otp == request.session.get('otp_code'):
            if table:
                return redirect('public_menu_table', qr_code=qr_code, table_code=table_code)
            return redirect('public_menu', qr_code=qr_code)
        else:
            messages.error(request, 'Invalid OTP')

    return render(request, 'menu/otp_verify.html', {
        'qr_code': qr_code,
        'hotel': hotel,
        'table': table,
        'table_code': table_code
    })


# -----------------------------
# PUBLIC MENU
# -----------------------------

def public_menu(request, qr_code, table_code=None):
    # Require OTP verification (simple gate using phone in session)
    if not request.session.get('otp_phone'):
        if table_code:
            return redirect('mobile_login_table', qr_code=qr_code, table_code=table_code)
        return redirect('mobile_login', qr_code=qr_code)

    hotel = get_object_or_404(Hotel, qr_code=qr_code)
    table = None
    if table_code:
        table = get_object_or_404(DiningTable, hotel=hotel, table_code=table_code)
        request.session['table_id'] = table.id  # keep table in session as fallback

    categories = Category.objects.filter(hotel=hotel).order_by('id')

    # Build a minimal cart_items map for the template (item_id -> qty)
    cart = request.session.get('cart', {})
    cart_items = {int(k): v['quantity'] for k, v in cart.items()} if cart else {}

    order = Order.objects.filter(hotel=hotel, table=table).order_by('-id').first()

    return render(request, 'menu/public_menu.html', {
        'hotel': hotel,
        'categories': categories,
        'cart_items': cart_items,
        'qr_code': qr_code,
        'table': table,
        'table_code': table_code,
        'order_id': order.id if order else None,
    })


# -----------------------------
# CART FUNCTIONS
# -----------------------------

def add_to_cart(request, qr_code, item_id, table_code=None):
    item = get_object_or_404(MenuItem, id=item_id)

    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    image_url = item.image.url if item.image else ''
    if item_id_str in cart:
        cart[item_id_str]['quantity'] += 1
    else:
        cart[item_id_str] = {
            'name': item.name,
            'price': float(item.price),
            'quantity': 1,
            'image': image_url,
        }
    request.session['cart'] = cart

    subtotal = sum(i['price'] * i['quantity'] for i in cart.values())
    gst = round(subtotal * 0.05)
    total = subtotal + gst
    cart_count = sum(i['quantity'] for i in cart.values())
    item_quantity = cart[item_id_str]['quantity']

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'item_id': item_id_str,
            'item_quantity': item_quantity,
            'cart_count': cart_count,
            'subtotal': int(subtotal),
            'gst': int(gst),
            'total': int(total),
        })

    if table_code:
        return redirect('view_cart_table', qr_code=qr_code, table_code=table_code)
    return redirect('view_cart', qr_code=qr_code)


def remove_from_cart(request, qr_code, item_id, table_code=None):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    remove_all = request.POST.get('remove_all')

    if item_id_str in cart:
        if remove_all:
            del cart[item_id_str]
            item_quantity = 0
        else:
            cart[item_id_str]['quantity'] -= 1
            if cart[item_id_str]['quantity'] <= 0:
                del cart[item_id_str]
                item_quantity = 0
            else:
                item_quantity = cart[item_id_str]['quantity']
    else:
        item_quantity = 0

    request.session['cart'] = cart

    subtotal = sum(i['price'] * i['quantity'] for i in cart.values())
    gst = round(subtotal * 0.05)
    total = subtotal + gst
    cart_count = sum(i['quantity'] for i in cart.values())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'item_id': item_id_str,
            'item_quantity': item_quantity,
            'cart_count': cart_count,
            'subtotal': int(subtotal),
            'gst': int(gst),
            'total': int(total),
        })

    if table_code:
        return redirect('view_cart_table', qr_code=qr_code, table_code=table_code)
    return redirect('view_cart', qr_code=qr_code)


def view_cart(request, qr_code, table_code=None):
    cart = request.session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    gst = round(subtotal * 0.05)
    total = subtotal + gst
    return render(request, 'menu/cart.html', {
        'cart': cart,
        'subtotal': int(subtotal),
        'gst': int(gst),
        'total': int(total),
        'qr_code': qr_code,
        'table_code': table_code
    })


# -----------------------------
# PAYMENT & ORDER
# -----------------------------

def payment_page(request, qr_code, table_code=None):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Cart is empty.")
        if table_code:
            return redirect('public_menu_table', qr_code=qr_code, table_code=table_code)
        return redirect('public_menu', qr_code=qr_code)

    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    gst = round(subtotal * 0.05, 2)
    total = round(subtotal + gst, 2)

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'gst': gst,
        'total': total,
        'qr_code': qr_code,
        'table_code': table_code
    }
    return render(request, 'menu/payment_page.html', context)


def confirm_order(request, qr_code, table_code=None):
    if request.method != 'POST':
        if table_code:
            return redirect('public_menu_table', qr_code=qr_code, table_code=table_code)
        return redirect('public_menu', qr_code=qr_code)

    cart = request.session.get('cart', {})
    guest_count = int(request.POST.get('guest_count', 1))
    payment_method = request.POST.get('payment_method')

    if not cart:
        messages.error(request, "Cart is empty.")
        if table_code:
            return redirect('public_menu_table', qr_code=qr_code, table_code=table_code)
        return redirect('public_menu', qr_code=qr_code)

    hotel = get_object_or_404(Hotel, qr_code=qr_code)

    # Resolve table from URL or session (fallback)
    table = None
    if table_code:
        table = get_object_or_404(DiningTable, hotel=hotel, table_code=table_code)
    else:
        table_id = request.session.get('table_id')
        if table_id:
            table = DiningTable.objects.filter(hotel=hotel, id=table_id).first()

    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    gst = round(subtotal * 0.05, 2)
    total = round(subtotal + gst, 2)

    order = Order.objects.create(
        hotel=hotel,
        table=table,  # ensure table is saved on the order
        guest_count=guest_count,
        payment_method=payment_method,
        subtotal=subtotal,
        gst=gst,
        total_amount=total,
        status='New'
    )

    for item_id, item in cart.items():
        menu_item = get_object_or_404(MenuItem, id=int(item_id))
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item['quantity'],
            price=item['price']
        )

    # Clear cart after creating the order
    request.session.pop('cart', None)

    if payment_method == 'COD':
        return redirect('order_success', order_id=order.id)
    # Online: go to correct card-payment route
    if table_code:
        return redirect('card_payment_table', qr_code=qr_code, table_code=table_code, order_id=order.id)
    return redirect('card_payment', qr_code=qr_code, order_id=order.id)


def card_payment(request, qr_code, order_id, table_code=None):
    return render(request, 'menu/card_payment.html', {
        'order_id': order_id,
        'qr_code': qr_code,
        'table_code': table_code
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'menu/order_success.html', {'order': order})


def track_order_view(request, qr_code, order_id, table_code=None):
    order = get_object_or_404(Order, id=order_id, hotel__qr_code=qr_code)
    steps = ['New', 'Preparing', 'Ready', 'Served']
    status_path = steps[:steps.index(order.status)] if order.status in steps else []
    return render(request, 'menu/track_order_status.html', {
        'order': order,
        'steps': steps,
        'qr_code': qr_code,
        'table_code': table_code,
        'order_status_path': status_path,
    })


# -----------------------------
# STAFF ORDER MGMT
# -----------------------------

@staff_member_required
def staff_orders(request):
    active_statuses = ['New', 'Preparing', 'Ready']
    completed_statuses = ['Served']

    # Prefetch everything needed for the template
    base = (Order.objects
            .select_related('hotel', 'table')
            .prefetch_related('items__menu_item'))

    orders_active = base.filter(status__in=active_statuses).order_by('-created_at')
    orders_completed = base.filter(status__in=completed_statuses).order_by('-created_at')

    status_choices = ['New', 'Preparing', 'Ready', 'Served']
    return render(request, 'menu/staff_orders.html', {
        'orders_active': orders_active,
        'orders_completed': orders_completed,
        'status_choices': status_choices,
    })


@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['New', 'Preparing', 'Ready', 'Served']:
            order.status = new_status
            order.save()
    return redirect('staff_orders')


# -----------------------------
# ADMIN LOGIN & DASHBOARD
# -----------------------------

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin user.")
    return render(request, 'menu/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


def admin_dashboard(request):
    return render(request, 'menu/admin_dashboard.html')


@login_required
def admin_settings(request):
    return render(request, 'menu/admin_settings.html')


# -----------------------------
# MENU ITEM MGMT
# -----------------------------

@login_required
def menu_items(request):
    tag_filter = request.GET.get('tag', '').strip()
    items = MenuItem.objects.all()
    if tag_filter:
        items = items.filter(tags__name__iexact=tag_filter)
    categories = Category.objects.all()
    return render(request, 'menu/menu_items.html', {
        'items': items,
        'tag_filter': tag_filter,
        'categories': categories,
    })


@login_required
def add_menu_item(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('menu_items')
    else:
        form = MenuItemForm()
    return render(request, 'menu/add_menu_item.html', {'form': form})


@login_required
def edit_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('menu_items')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'menu/edit_menu_item.html', {'form': form, 'item': item})


@login_required
def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        return redirect('menu_items')
    return render(request, 'menu/delete_menu_item.html', {'item': item})


# -----------------------------
# CATEGORY MGMT
# -----------------------------

@login_required
def menu_categories(request):
    categories = Category.objects.all()
    return render(request, 'menu/menu_categories.html', {'categories': categories})


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('menu_categories')
    else:
        form = CategoryForm()
    return render(request, 'menu/add_category.html', {'form': form})


@login_required
def edit_category(request, cat_id):
    category = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('menu_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'menu/edit_category.html', {'form': form, 'category': category})


@login_required
def delete_category(request, cat_id):
    category = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        category.delete()
        return redirect('menu_categories')
    return render(request, 'menu/delete_category.html', {'category': category})


# -----------------------------
# AI DESCRIPTION GENERATOR (admin)
# -----------------------------

@csrf_exempt
@login_required
def ai_generate_description(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    name = data.get('name', '')
    category = data.get('category', '')

    prompt = f"Write a delicious, enticing menu description for a dish called '{name}'."
    if category:
        prompt += f" It is in the '{category}' category."
    prompt += " Make it sound appetizing, concise, and unique. 2-3 sentences."

    api_key = os.getenv("COHERE_API_KEY")
    description = ""
    if api_key:
        try:
            resp = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "command-r-plus",
                    "prompt": prompt,
                    "max_tokens": 120,
                    "temperature": 0.6,
                },
                timeout=15,
            )
            resp.raise_for_status()
            description = (resp.json().get("generations", [{}])[0].get("text") or "").strip()
        except Exception as e:
            description = f"AI description not available (error: {str(e)})"
    else:
        description = "A tasty dish prepared with care. Description pending."

    return JsonResponse({"description": description})


# -----------------------------
# AI IMAGE GENERATOR (admin demo)
# -----------------------------

@csrf_exempt
@login_required
def ai_generate_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    prompt = data.get('prompt') or f"A high quality food photo of {data.get('name', '')}"
    images = []
    for i in range(5):
        image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?seed={i}"
        images.append(image_url)
    return JsonResponse({"images": images})


# -----------------------------
# AI TAG GENERATOR (public)
# -----------------------------

@require_POST
def generate_ai_tags(request):
    # Accept both form-encoded and application/json
    try:
        data = json.loads(request.body.decode("utf-8")) if request.content_type and "application/json" in request.content_type else {}
    except Exception:
        data = {}

    name = (request.POST.get("name") or data.get("name") or "").strip()
    category = (request.POST.get("category") or data.get("category") or "").strip()

    if not name or not category:
        return JsonResponse({"error": "Missing name or category"}, status=400)

    prompt = f"""
You are a food menu tagging assistant.
Based on the name and category, suggest relevant tags with emoji.
Always apply these rules if matched:
- If category or name suggests it is Non-Veg → add "Spicy 🌶️"
- If category or name suggests it is Veg → add "Vegan 🥦"
- If category or name includes drinks, juice, or specific beverages like mango juice → add "Cool Drinks 🥤"
- If category or name includes ice cream, sundae, or dessert for kids → add "Kids’ Favorite 🧒"

Menu item:
Name: {name}
Category: {category}

Output ONLY a JSON array of objects with "name" and "emoji" fields.
Example:
[
  {{"name": "Vegan", "emoji": "🥦"}},
  {{"name": "Spicy", "emoji": "🌶️"}}
]
""".strip()

    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return JsonResponse({"tags": []})  # Fail silently for the public UI

    try:
        response = requests.post(
            "https://api.cohere.ai/v1/generate",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "command-r-plus",
                "prompt": prompt,
                "max_tokens": 80,
                "temperature": 0.4,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        return JsonResponse({"tags": []})

    generation_text = (response.json().get("generations", [{}])[0].get("text") or "").strip()

    # Strip code fences safely
    if generation_text.startswith("```"):
        lines = generation_text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        generation_text = "\n".join(lines).strip()

    # Parse JSON or fallback
    tags = []
    try:
        parsed = json.loads(generation_text)
        if isinstance(parsed, list):
            tags = parsed
    except json.JSONDecodeError:
        start = generation_text.find("[")
        end = generation_text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                tags = json.loads(generation_text[start:end+1])
            except Exception:
                tags = []

    # Normalize
    if isinstance(tags, list):
        tags = [
            {"name": (t.get("name") or "").strip(), "emoji": (t.get("emoji") or "").strip()}
            for t in tags if isinstance(t, dict)
        ]
    else:
        tags = []

    return JsonResponse({"tags": tags})