from django.urls import path
from . import views
from .views import stripe_webhook

urlpatterns = [
    path('', views.fitness_class_list, name='fitness_class_list'),
    path('<int:class_id>/', views.fitness_class_detail, name='fitness_class_detail'),
    path('<int:class_id>/book/', views.book_fitness_class, name='book_class'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('create/', views.create_class, name='create_class'),
    path('create-checkout-session/', views.start_checkout_session, name='start_checkout_session'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]




