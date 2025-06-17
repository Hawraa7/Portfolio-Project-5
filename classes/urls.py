from django.urls import path
from . import views

urlpatterns = [
    path('', views.class_list, name='class_list'),
    path('book/<int:class_id>/', views.book_class, name='book_class'),
    path('cancel/<int:class_id>/', views.cancel_booking, name='cancel_booking'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('create/', views.create_class, name='create_class'),
]

