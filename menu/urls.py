from django.urls import path
from . import views

urlpatterns = [
    path('<str:qr_code>/', views.mobile_login, name='mobile_login'),
    path('<str:qr_code>/otp/', views.otp_verify, name='otp_verify'),
    path('<str:qr_code>/public/', views.public_menu, name='public_menu'),
    path('<str:qr_code>/add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('<str:qr_code>/remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('<str:qr_code>/cart/', views.view_cart, name='view_cart'),
]