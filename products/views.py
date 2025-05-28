from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def all_products(request):
    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'products/products.html', context)

def products_by_category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    products = Product.objects.filter(category=category)
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'products/products_by_category.html', context)
