from django.shortcuts import render, redirect, reverse, get_object_or_404, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from .forms import OrderForm
from .models import Order, OrderLineItem
from products.models import Product
from profiles.forms import UserProfileForm
from profiles.models import UserProfile, Subscription
from bag.contexts import bag_contents
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
import stripe
import json
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone


import stripe
import json
import random


@require_POST
def cache_checkout_data(request):
   try:
       pid = request.POST.get('client_secret').split('_secret')[0]
       stripe.api_key = settings.STRIPE_SECRET_KEY
       stripe.PaymentIntent.modify(pid, metadata={
           'bag': json.dumps(request.session.get('bag', {})),
           'save_info': request.POST.get('save_info'),
           'username': request.user,
       })
       return HttpResponse(status=200)
   except Exception as e:
       messages.error(request, 'Sorry, your payment cannot be \
           processed right now. Please try again later.')
       return HttpResponse(content=e, status=400)


def _to_decimal(value):
   return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)




def checkout(request):
   """Handles checkout: apply promotions, compute totals, create order and payment intent."""
   stripe_public_key = settings.STRIPE_PUBLIC_KEY
   stripe_secret_key = settings.STRIPE_SECRET_KEY
   bag = request.session.get("bag", {})


   if not bag:
       messages.error(request, "Your bag is empty.")
       return redirect(reverse("products"))


   # --- Compute totals ---
   category_totals = {}
   line_items_for_order = []
   subtotal = Decimal("0.00")


   for item_id, item_data in bag.items():
       product = get_object_or_404(Product, id=item_id)
       price = Decimal(str(product.price))


       if isinstance(item_data, int):
           qty = item_data
       else:
           qty = sum(item_data.get("items_by_size", {}).values())


       item_total = price * qty
       subtotal += item_total
       line_items_for_order.append({"product": product, "quantity": qty, "size": None})


       category = getattr(product, "category", None)
       if category:
           entry = category_totals.setdefault(category.id, {"category": category, "subtotal": Decimal("0.00")})
           entry["subtotal"] += item_total


   current_bag = bag_contents(request)
   delivery = _to_decimal(current_bag.get("delivery", 0))


   # --- Apply category promotions ---
   promotion_discount = Decimal("0.00")
   promotion_breakdown = []
   subscription = None
   if request.user.is_authenticated:
       subscription, _ = Subscription.objects.get_or_create(user=request.user)
       # --- Update validity of all user's promotions first ---
       for promo in subscription.promotions.all():
           promo.check_validity()  # This will mark expired promotions as invalid
          
       for cat_info in category_totals.values():
           category = cat_info["category"]
           subtotal_cat = cat_info["subtotal"]
           promos = subscription.promotions.filter(category=category, active=True, validity=True)
           for promo in promos:
               discount = (Decimal(promo.percentage) / Decimal("100")) * subtotal_cat
               discount = discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
               if discount > 0:
                   promotion_discount += discount
                   promotion_breakdown.append({"promo": promo, "category": category, "discount": discount})


   total_after_promos = subtotal - promotion_discount
   total_after_promos = total_after_promos.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


   # --- Apply wallet (if active & enough funds) ---
   # Retrieve whether the user opted to use the wallet
   use_wallet = request.POST.get("use_wallet") == "on"
   wallet_used = Decimal("0.00")


   if use_wallet and subscription and subscription.wallet > 0:
       wallet_used = min(subscription.wallet, total_after_promos + delivery)
       wallet_used = wallet_used.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
   else:
       wallet_used = Decimal("0.00")




   grand_total = total_after_promos + delivery - wallet_used
   if grand_total < 0:
       grand_total = Decimal("0.00")


   # --- Create Stripe intent ---
   stripe.api_key = stripe_secret_key
   amount = int((grand_total * 100).to_integral_value(rounding=ROUND_HALF_UP))
   intent = stripe.PaymentIntent.create(amount=amount, currency=settings.STRIPE_CURRENCY) if amount > 0 else None


   # --- Handle POST ---
   if request.method == "POST":
       order_form = OrderForm(request.POST)
       if order_form.is_valid():
           with transaction.atomic():
               order = order_form.save(commit=False)
               order.original_bag = json.dumps(bag)
               order.order_total = subtotal
               order.delivery_cost = delivery
               order.grand_total = grand_total
               order.stripe_pid = intent.id if intent else ""
               order.loyalty_discount = promotion_discount + wallet_used
               order.save()


               for li in line_items_for_order:
                   OrderLineItem.objects.create(
                       order=order,
                       product=li["product"],
                       quantity=li["quantity"],
                       product_size=li["size"],
                   )


               request.session["recent_order_number"] = order.order_number
               request.session["promotion_ids_used"] = [p["promo"].id for p in promotion_breakdown]
               request.session["wallet_used"] = float(wallet_used)
               request.session.pop("bag", None)


               return redirect(reverse("checkout_success", args=[order.order_number]))
       else:
           messages.error(request, "There was an error with your order form. Please try again.")
   else:
       order_form = OrderForm()


   context = {
       "order_form": order_form,
       "stripe_public_key": stripe_public_key,
       "client_secret": intent.client_secret if intent else None,
       "subtotal": subtotal,
       "delivery": delivery,
       "promotion_discount": promotion_discount,
       "promotion_breakdown": promotion_breakdown,
       "wallet_used": wallet_used,
       "grand_total": grand_total,
       "total_after_promos": total_after_promos,
   }
   return render(request, "checkout/checkout.html", context)


@login_required
def checkout_success(request, order_number):
   """Finalize order and update loyalty data after successful payment."""
   order = get_object_or_404(Order, order_number=order_number)
   profile, _ = UserProfile.objects.get_or_create(user=request.user)
   subscription, _ = Subscription.objects.get_or_create(user=request.user)


   order.user_profile = profile
   order.save(update_fields=["user_profile"])


   # --- Deduct wallet (only once, after success) ---
   wallet_used = Decimal(str(request.session.get("wallet_used", 0)))
   total_spent = Decimal(str(order.grand_total))
   redeemed_wallet = subscription.redeem_points(total_spent)
   print(redeemed_wallet)
   print(total_spent)
   if wallet_used > 0:
       subscription.wallet = (Decimal(str(subscription.wallet)) - wallet_used + redeemed_wallet).quantize(Decimal("0.01"))
       if subscription.wallet < 0:
           subscription.wallet = Decimal("0.00")
       messages.success(request, f"💶 €{wallet_used} deducted from your wallet.")
   subscription.save(update_fields=["wallet"])
   # --- Mark promotions as used ---
   promo_ids = request.session.get("promotion_ids_used", [])
   if promo_ids:
       used_promos = subscription.promotions.filter(id__in=promo_ids)
       for promo in used_promos:
           promo.validity = False
           promo.save(update_fields=["validity"])
       messages.info(request, f"🎟 {len(used_promos)} promotions marked as used.")


   # --- Award points for completed or fully covered order ---
   if total_spent >= 0:
       subscription.add_points(total_spent)
       subscription.save()
       messages.success(request, f"⭐ You earned {int(total_spent)} points!")


   # --- Grant new promotion (if any) ---
   new_promo = subscription.get_random_promotion()
   if new_promo:
       messages.success(
           request,
           f"🎁 New promotion unlocked: {new_promo.percentage}% off {new_promo.category.name}!"
       )


   messages.success(request, f"✅ Order {order_number} completed successfully.")
   messages.info(request, f"💰 Wallet balance: €{subscription.wallet}")
   messages.info(request, f"⭐ Current points: {subscription.points}")


   # --- Cleanup session ---
   for key in ("bag", "recent_order_number", "promotion_ids_used", "wallet_used"):
       request.session.pop(key, None)


   return render(request, "checkout/checkout_success.html", {
       "order": order,
       "subscription": subscription,
       "new_promo": new_promo,
   })



