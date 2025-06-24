from django.urls import path
from . import views

urlpatterns = [
    path('', views.class_list, name='class_list'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('book/<int:class_id>/', views.book_class, name='book_class'),
    path('cancel_booking/<int:class_id>/', views.cancel_booking, name='cancel_booking'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('create_class/', views.create_class, name='create_class'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('classes/success', views.payment_success, name='payment_success'),
    path('create-subscription-session/', views.create_subscription_session, name='create_subscription_session'),

    path('success/', views.booking_success, name='booking_success'),
    path('subscription_success/', views.subscription_success, name='subscription_success'),
    path('cancel/', views.booking_cancel, name='booking_cancel'),
    path('subscription_cancel/', views.subscription_cancel, name='subscription_cancel'),

    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('create-subscription-checkout-session/<int:class_id>/', views.create_subscription_checkout_session, name='create_subscription_checkout_session'),

]


