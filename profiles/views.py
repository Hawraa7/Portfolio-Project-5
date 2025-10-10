from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserProfileForm
import json
from django.http import JsonResponse
from checkout.models import Order
from profiles.models import Subscription, Promotion

def delete_duplicate_orders():
    """
    Detect and remove duplicate orders created within the same minute
    for the same user (or same email for guest checkouts).
    Keeps the one with the lower grand_total.
    """
    orders = Order.objects.all().order_by('email', 'date')
    duplicates_found = 0
    deleted_count = 0

    for user_email in orders.values_list('email', flat=True).distinct():
        user_orders = Order.objects.filter(email=user_email).order_by('date')

        for i in range(len(user_orders) - 1):
            current_order = user_orders[i]
            next_order = user_orders[i + 1]

            # Compare if they are within the same minute
            if abs((next_order.date - current_order.date).total_seconds()) < 60:
                duplicates_found += 1

                # Decide which one to delete (delete the one with higher grand_total)
                if next_order.grand_total > current_order.grand_total:
                    next_order.delete()
                    deleted_count += 1
                    print(f"Deleted duplicate order {next_order.order_number} "
                          f"(higher price: {next_order.grand_total})")
                else:
                    current_order.delete()
                    deleted_count += 1
                    print(f"Deleted duplicate order {current_order.order_number} "
                          f"(higher price: {current_order.grand_total})")
                    
@login_required
def profile(request):
   """ Display the user's profile. """
   profile = get_object_or_404(UserProfile, user=request.user)
   subscription = getattr(request.user, 'subscription', None)
   delete_duplicate_orders()

   if request.method == 'POST':
       form = UserProfileForm(request.POST, instance=profile)
       if form.is_valid():
           form.save()
           messages.success(request, 'Profile updated successfully')
       else:
           messages.error(request, 'Update failed. Please ensure the form is valid.')
   else:
       form = UserProfileForm(instance=profile)

   # Get filtered promotions
   valid_promotions = subscription.promotions.filter(validity=True) if subscription else []
   orders = profile.orders.all()

   template = 'profiles/profile.html'
   context = {
       'form': form,
       'orders': orders,
       'on_profile_page': True,
       'subscription': subscription,
       'valid_promotions': valid_promotions,
   }

   return render(request, template, context)


@login_required
def toggle_promotion(request):
   """
   Activate/deactivate a promotion for the user's subscription.
   Only one promotion can be active per category.
   """
   if request.method == "POST":
       data = json.loads(request.body)
       promo_id = data.get("promo_id")
       subscription = get_object_or_404(Subscription, user=request.user)
       promo = get_object_or_404(Promotion, id=promo_id, validity=True)

       if promo.active:
           # Deactivate promotion
           promo.active = False
           promo.save()
           return JsonResponse({"status": "deactivated"})
       else:
           # Deactivate any other active promotion in the same category
           subscription.promotions.filter(category=promo.category, active=True).update(active=False)
           # Activate this promotion
           promo.active = True
           promo.save()
           return JsonResponse({"status": "activated"})

   return JsonResponse({"error": "Invalid request"}, status=400)


def order_history(request, order_number):
   order = get_object_or_404(Order, order_number=order_number)

   messages.info(request, (
       f'This is a past confirmation for order number {order_number}. '
       'A confirmation email was sent on the order date.'
   ))

   template = 'checkout/checkout_success.html'
   context = {
       'order': order,
       'from_profile': True,
   }

   return render(request, template, context)
