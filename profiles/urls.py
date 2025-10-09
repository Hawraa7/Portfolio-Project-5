from django.urls import path
from . import views


urlpatterns = [
   path('', views.profile, name='profile'),
   path('toggle-promotion/', views.toggle_promotion, name='toggle_promotion'),
   path('order_history/<order_number>', views.order_history, name='order_history'),
]

