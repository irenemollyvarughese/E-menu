from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import MenuItem, Category, Hotel

from django.shortcuts import render, redirect
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from .models import Hotel

def mobile_login(request, qr_code):
    hotel = get_object_or_404(Hotel, qr_code=qr_code)  # Fetch the hotel
    if request.method == 'POST':
        phone = request.POST.get('phone')
        # Generate OTP, send SMS (use Twilio or similar)
        request.session['otp_phone'] = phone
        # Save OTP in session or DB
        request.session['otp_code'] = '1234'  # Replace with real OTP
        return redirect('otp_verify', qr_code=qr_code)
    return render(request, 'menu/mobile_login.html', {'qr_code': qr_code, 'hotel': hotel})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Hotel
from django.contrib import messages

def otp_verify(request, qr_code):
    hotel = get_object_or_404(Hotel, qr_code=qr_code)  # Fetch the hotel
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp == request.session.get('otp_code'):
            # OTP correct, redirect to menu
            return redirect('public_menu', qr_code=qr_code)
        else:
            messages.error(request, 'Invalid OTP')
    return render(request, 'menu/otp_verify.html', {'qr_code': qr_code, 'hotel': hotel})



def public_menu(request, qr_code):
    # Block access if not logged in via OTP
    if not request.session.get('otp_phone'):
        return redirect('mobile_login', qr_code=qr_code)
    hotel = get_object_or_404(Hotel, qr_code=qr_code)
    categories = Category.objects.filter(hotel=hotel).order_by('id')
    cart = request.session.get('cart', {})
    cart_items = {int(k): v['quantity'] for k, v in cart.items()} if cart else {}
    return render(request, 'menu/public_menu.html', {
        'hotel': hotel,
        'categories': categories,
        'cart_items': cart_items,
        'qr_code': qr_code,
    })

def add_to_cart(request, qr_code, item_id):
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
    return redirect('view_cart', qr_code=qr_code)

def remove_from_cart(request, qr_code, item_id):
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
    return redirect('view_cart', qr_code=qr_code)

def view_cart(request, qr_code):
    cart = request.session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    gst = round(subtotal * 0.05)  # 5% GST, adjust as needed
    total = subtotal + gst
    return render(request, 'menu/cart.html', {
        'cart': cart,
        'subtotal': int(subtotal),
        'gst': int(gst),
        'total': int(total),
        'qr_code': qr_code,
    })