from django.urls import path
from . import views

urlpatterns = [
    path('', views.class_list, name='class_list'),
    path('<int:pk>/', views.class_detail, name='class_detail'),
    path('<int:pk>/book/', views.book_class, name='book_class'),
    path('create/', views.create_class, name='create_class'),
]



