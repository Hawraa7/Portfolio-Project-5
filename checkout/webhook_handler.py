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
        """
        Handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200)
    
    def handle_payment_intent_succeeded(self, event):
        try:
            intent = event.data.object
            pid = intent.id
            bag = intent.metadata.bag
            save_info = intent.metadata.save_info

            billing_details = intent.charges.data[0].billing_details
            shipping_details = intent.shipping
            grand_total = round(intent.charges.data[0].amount / 100, 2)

            # Clean empty shipping fields
            for field, value in shipping_details.address.items():
                if value == "":
                    shipping_details.address[field] = None

            profile = None
            username = getattr(intent.metadata, 'username', None)
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

            order = None
            order_exists = False
            for attempt in range(10):
                try:
                    order = Order.objects.get(
                        full_name__iexact=shipping_details.name,
                        email__iexact=billing_details.email,
                        phone_number__iexact=shipping_details.phone,
                        country__iexact=shipping_details.address.country,
                        postcode__iexact=shipping_details.address.postal_code,
                        town_or_city__iexact=shipping_details.address.city,
                        street_address1__iexact=shipping_details.address.line1,
                        street_address2__iexact=shipping_details.address.line2,
                        county__iexact=shipping_details.address.state,
                        grand_total=grand_total,
                        original_bag=bag,
                        stripe_pid=pid,
                    )
                    order_exists = True
                    break
                except Order.DoesNotExist:
                    time.sleep(1)

            if not order_exists:
                order = Order.objects.create(
                    full_name=shipping_details.name,
                    user_profile=profile,
                    email=billing_details.email,
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

            self._send_confirmation_email(order)

        except Exception as e:
            self._send_confirmation_email(order)
            # Always return 200 to Stripe to prevent retries
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | ERROR: {e}',
                status=200
            )

        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS',
            status=200
        )

    
    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)