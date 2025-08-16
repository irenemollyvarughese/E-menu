from django.urls import path
from . import views

urlpatterns = [
    # Staff/Admin (specific, keep first)
    path('staff/login/', views.admin_login, name='admin_login'),
    path('staff/logout/', views.admin_logout, name='admin_logout'),
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('staff/orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('staff/menu/items/', views.menu_items, name='menu_items'),
    path('staff/menu/items/add/', views.add_menu_item, name='add_menu_item'),
    path('staff/menu/items/<int:item_id>/edit/', views.edit_menu_item, name='edit_menu_item'),
    path('staff/menu/items/<int:item_id>/delete/', views.delete_menu_item, name='delete_menu_item'),
    path('staff/menu/categories/', views.menu_categories, name='menu_categories'),
    path('staff/menu/categories/add/', views.add_category, name='add_category'),
    path('staff/menu/categories/<int:cat_id>/edit/', views.edit_category, name='edit_category'),
    path('staff/menu/categories/<int:cat_id>/delete/', views.delete_category, name='delete_category'),
    path('staff/menu/items/ai-generate-description/', views.ai_generate_description, name='ai_generate_description'),
    path('staff/menu/items/ai-generate-image/', views.ai_generate_image, name='ai_generate_image'),
    path('staff/menu/item/generate-tags/', views.generate_ai_tags, name='staff_generate_ai_tags'),

    # Public AI tags endpoint
    path('ai-tags/', views.generate_ai_tags, name='generate_ai_tags'),

    # Specific customer routes (put BEFORE the generic login routes)
    # OTP
    path('<str:qr_code>/<slug:table_code>/otp/', views.otp_verify, name='otp_verify_table'),
    path('<str:qr_code>/otp/', views.otp_verify, name='otp_verify'),

    # Public menu
    path('<str:qr_code>/<slug:table_code>/public/', views.public_menu, name='public_menu_table'),
    path('<str:qr_code>/public/', views.public_menu, name='public_menu'),

    # Cart
    path('<str:qr_code>/<slug:table_code>/add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart_table'),
    path('<str:qr_code>/add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('<str:qr_code>/<slug:table_code>/remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart_table'),
    path('<str:qr_code>/remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('<str:qr_code>/<slug:table_code>/cart/', views.view_cart, name='view_cart_table'),
    path('<str:qr_code>/cart/', views.view_cart, name='view_cart'),

    # Payment flow
    path('<str:qr_code>/<slug:table_code>/payment/', views.payment_page, name='payment_page_table'),
    path('<str:qr_code>/payment/', views.payment_page, name='payment_page'),
    path('<str:qr_code>/<slug:table_code>/confirm-order/', views.confirm_order, name='confirm_order_table'),
    path('<str:qr_code>/confirm-order/', views.confirm_order, name='confirm_order'),
    path('<str:qr_code>/<slug:table_code>/card-payment/<int:order_id>/', views.card_payment, name='card_payment_table'),
    path('<str:qr_code>/card-payment/<int:order_id>/', views.card_payment, name='card_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('order-status/<str:qr_code>/<slug:table_code>/<int:order_id>/', views.track_order_view, name='track_order_table'),
    path('order-status/<str:qr_code>/<int:order_id>/', views.track_order_view, name='track_order'),

    # Generic login routes LAST (catch-alls)
    path('<str:qr_code>/<slug:table_code>/', views.mobile_login, name='mobile_login_table'),
    path('<str:qr_code>/', views.mobile_login, name='mobile_login'),
]