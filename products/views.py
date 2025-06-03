from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def all_products(request):
    """ View to show all products """
    products = Product.objects.all()
    category = request.GET.get('category', None)

    if category:
        products = products.filter(category__name=category)

    context = {
        'products': products,
        'current_category': category,
    }
    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ View to show individual product details """
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'products/product_detail.html', {'product': product})

