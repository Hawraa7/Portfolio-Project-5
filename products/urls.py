from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_products, name='products'),
    path('<str:category_name>/', views.products_by_category, name='products_by_category'),
]
