from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import UserProfile
import json
import stripe

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
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """Handle payment_intent.succeeded webhook"""
        intent = event.data.object
        pid = intent.id

        # --- Extract metadata ---
        bag = getattr(intent.metadata, "bag", "{}")
        save_info = getattr(intent.metadata, "save_info", False)
        username = getattr(intent.metadata, 'username', None)

        # --- Extract billing email ---
        billing_email = "no-email@example.com"
        if getattr(intent, "charges", None) and getattr(intent.charges.data[0], "billing_details", None):
            billing_email = intent.charges.data[0].billing_details.email or billing_email

        # --- Extract shipping details safely ---
        shipping = getattr(intent, "shipping", None)
        shipping_details = type("Shipping", (), {})()
        shipping_details.name = getattr(shipping, "name", "")
        shipping_details.phone = getattr(shipping, "phone", "")
        address = getattr(shipping, "address", None)
        shipping_details.address = type("Address", (), {})()
        shipping_details.address.country = getattr(address, "country", None)
        shipping_details.address.postal_code = getattr(address, "postal_code", None)
        shipping_details.address.city = getattr(address, "city", None)
        shipping_details.address.line1 = getattr(address, "line1", None)
        shipping_details.address.line2 = getattr(address, "line2", None)
        shipping_details.address.state = getattr(address, "state", None)

        # --- Extract grand total ---
        if getattr(intent, "charges", None) and getattr(intent.charges, "data", None) and intent.charges.data:
            grand_total = round(intent.charges.data[0].amount / 100, 2)
        else:
            grand_total = round(getattr(intent, "amount", 0) / 100, 2)

        # --- Update user profile if authenticated ---
        profile = None
        if username and username != 'AnonymousUser':
            profile = UserProfile.objects.filter(user__username=username).first()
            if profile and save_info:
                profile.default_phone_number = shipping_details.phone or ''
                profile.default_country = shipping_details.address.country or ''
                profile.default_postcode = shipping_details.address.postal_code or ''
                profile.default_town_or_city = shipping_details.address.city or ''
                profile.default_street_address1 = shipping_details.address.line1 or ''
                profile.default_street_address2 = shipping_details.address.line2 or ''
                profile.default_county = shipping_details.address.state or ''
                profile.save()

        # --- Check if order already exists by Stripe PID ---
        order = Order.objects.filter(stripe_pid=pid).first()
        if order:
            # Order already exists; return success
            self._send_confirmation_email(order)
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | SUCCESS (order already exists)',
                status=200
            )

        # --- Create new order ---
        try:
            order = Order.objects.create(
                full_name=shipping_details.name or "Guest",
                user_profile=profile,
                email=billing_email,
                phone_number=shipping_details.phone or '',
                country=shipping_details.address.country or '',
                postcode=shipping_details.address.postal_code or '',
                town_or_city=shipping_details.address.city or '',
                street_address1=shipping_details.address.line1 or '',
                street_address2=shipping_details.address.line2 or '',
                county=shipping_details.address.state or '',
                grand_total=grand_total,
                original_bag=bag,
                stripe_pid=pid,
            )

            # --- Create line items ---
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
                        for size, quantity in item_data.get('items_by_size', {}).items():
                            OrderLineItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size
                            )
                except Product.DoesNotExist:
                    continue

            # --- Send confirmation email ---
            self._send_confirmation_email(order)

        except Exception as e:
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | ERROR: {e}',
                status=200
            )

        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS',
            status=200
        )

    def handle_payment_intent_payment_failed(self, event):
        """Handle payment_intent.payment_failed webhook"""
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200
        )
