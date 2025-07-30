from django.urls import path
from . import views

urlpatterns = [
    path('<str:qr_code>/', views.mobile_login, name='mobile_login'),
    path('<str:qr_code>/otp/', views.otp_verify, name='otp_verify'),
    path('<str:qr_code>/public/', views.public_menu, name='public_menu'),
    path('<str:qr_code>/add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('<str:qr_code>/remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('<str:qr_code>/cart/', views.view_cart, name='view_cart'),



    
    #  new add 


    path('menu/<str:qr_code>/payment/', views.payment_page, name='payment_page'),
    path('menu/<str:qr_code>/confirm-order/', views.confirm_order, name='confirm_order'),
    path('menu/<str:qr_code>/card-payment/<int:order_id>/', views.card_payment, name='card_payment'),
    path('menu/order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('order-status/<str:qr_code>/<int:order_id>/', views.track_order_view, name='track_order')
 # 👈 New

     
]