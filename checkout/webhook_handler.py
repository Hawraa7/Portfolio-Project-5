from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import UserProfile

import json
import time


class StripeWH_Handler:
    """Handle Stripe webhooks"""

    def __init__(self, request):
        self.request = request

    def _send_confirmation_email(self, order):
        """Send the user a confirmation email"""
        cust_email = order.email
        subject = render_to_string(
            'checkout/confirmation_emails/confirmation_email_subject.txt',
            {'order': order})
        body = render_to_string(
            'checkout/confirmation_emails/confirmation_email_body.txt',
            {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})
        
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [cust_email]
        )

    def handle_event(self, event):
        """Handle a generic/unknown/unexpected webhook event"""
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200
        )

    def handle_payment_intent_succeeded(self, event):
        try:
            intent = event.data.object
            pid = intent.id
            bag = intent.metadata.bag
            save_info = intent.metadata.save_info

            # --- FIX: Safe extraction of billing, shipping, total ---
            charge_data = getattr(intent, "charges", None)
            if charge_data and hasattr(charge_data, "data") and len(charge_data.data) > 0:
                billing_details = charge_data.data[0].billing_details
                grand_total = round(charge_data.data[0].amount / 100, 2)
            else:
                # Fallback if no charge info yet (rare but possible)
                billing_details = {
                    "email": getattr(intent, "receipt_email", None),
                    "name": getattr(intent, "shipping", {}).get("name", "Unknown") if hasattr(intent, "shipping") else "Unknown",
                }
                grand_total = round(getattr(intent, "amount", 0) / 100, 2)
                send_mail(
                    "⚠️ Stripe charge data missing",
                    f"No charges in intent for PID {pid}. Using fallback billing details.",
                    settings.DEFAULT_FROM_EMAIL,
                    ["hawraahijazi1996@gmail.com"]
                )

            shipping_details = getattr(intent, "shipping", None)
            if not shipping_details:
                send_mail(
                    "⚠️ Missing shipping details",
                    f"Intent {pid} has no shipping info.",
                    settings.DEFAULT_FROM_EMAIL,
                    ["hawraahijazi1996@gmail.com"]
                )
            # --- END FIX ---

            # Clean empty shipping fields
            if shipping_details and hasattr(shipping_details, "address"):
                for field, value in shipping_details.address.items():
                    if value == "":
                        shipping_details.address[field] = None

            # Get user profile if authenticated
            profile = None
            username = getattr(intent.metadata, 'username', None)
            if username and username != 'AnonymousUser':
                profile = UserProfile.objects.filter(user__username=username).first()
                if profile and save_info and shipping_details:
                    profile.default_phone_number = shipping_details.phone or ''
                    profile.default_country = shipping_details.address.country or ''
                    profile.default_postcode = shipping_details.address.postal_code or ''
                    profile.default_town_or_city = shipping_details.address.city or ''
                    profile.default_street_address1 = shipping_details.address.line1 or ''
                    profile.default_street_address2 = shipping_details.address.line2 or ''
                    profile.default_county = shipping_details.address.state or ''
                    profile.save()

            # Try to find existing order
            order = None
            order_exists = False
            for attempt in range(10):
                try:
                    order = Order.objects.get(
                        full_name__iexact=getattr(shipping_details, "name", ""),
                        email__iexact=billing_details["email"] if isinstance(billing_details, dict) else billing_details.email,
                        grand_total=grand_total,
                        original_bag=bag,
                        stripe_pid=pid,
                    )
                    order_exists = True
                    break
                except Order.DoesNotExist:
                    time.sleep(1)

            # Create order if not found
            if not order_exists:
                order = Order.objects.create(
                    full_name=getattr(shipping_details, "name", ""),
                    user_profile=profile,
                    email=billing_details["email"] if isinstance(billing_details, dict) else billing_details.email,
                    phone_number=getattr(shipping_details, "phone", ""),
                    country=getattr(shipping_details.address, "country", "") if hasattr(shipping_details, "address") else "",
                    postcode=getattr(shipping_details.address, "postal_code", "") if hasattr(shipping_details, "address") else "",
                    town_or_city=getattr(shipping_details.address, "city", "") if hasattr(shipping_details, "address") else "",
                    street_address1=getattr(shipping_details.address, "line1", "") if hasattr(shipping_details, "address") else "",
                    street_address2=getattr(shipping_details.address, "line2", "") if hasattr(shipping_details, "address") else "",
                    county=getattr(shipping_details.address, "state", "") if hasattr(shipping_details, "address") else "",
                    grand_total=grand_total,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                bag_items = json.loads(bag or '{}')
                for item_id, item_data in bag_items.items():
                    try:
                        product = Product.objects.get(id=item_id)
                        if isinstance(item_data, int):
                            OrderLineItem.objects.create(
                                order=order,
                                product=product,
                                quantity=item_data
                            )
                        else:
                            for size, quantity in item_data['items_by_size'].items():
                                OrderLineItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity,
                                    product_size=size
                                )
                    except Product.DoesNotExist:
                        continue  # skip missing products

            # Confirmation email
            self._send_confirmation_email(order)

        except Exception as e:
            # Send yourself a debug email when something fails
            send_mail(
                '❌ Stripe Webhook Error in handle_payment_intent_succeeded',
                f'Error details:\n{e}',
                settings.DEFAULT_FROM_EMAIL,
                ['hawraahijazi1996@gmail.com']
            )
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | ERROR: {e}',
                status=200
            )

        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS',
            status=200
        )

    def handle_payment_intent_payment_failed(self, event):
        """Handle the payment_intent.payment_failed webhook"""
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200
        )
