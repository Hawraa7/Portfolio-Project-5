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
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """Handle payment_intent.succeeded webhook"""
        try:
            intent = event.data.object
            pid = intent.id
            bag = getattr(intent.metadata, "bag", "{}")
            save_info = getattr(intent.metadata, "save_info", False)

            # Debug email: show the full intent object
            send_mail(
                'Test 5 from Zouzou’s Fitness',
                f'If you’re reading this, Gmail App Passwords work 🎉 {intent}',
                settings.DEFAULT_FROM_EMAIL,
                ['hawraahijazi1996@gmail.com']
            )

            # Safe extraction of billing email
            billing_email = getattr(intent, "receipt_email", None)
            if not billing_email and getattr(intent, "charges", None):
                if getattr(intent.charges, "data", None):
                    billing_email = intent.charges.data[0].billing_details.email
            billing_email = billing_email or "no-email@example.com"

            # Debug email after billing extraction
            # send_mail(
            #     'Test 3 from Zouzou’s Fitness',
            #     f'Billing email resolved: {billing_email}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     ['hawraahijazi1996@gmail.com']
            # )

            # Safe extraction of shipping details
            shipping_details = getattr(intent, "shipping", None)
            if not shipping_details:
                shipping_details = type("Shipping", (), {})()
                shipping_details.name = ""
                shipping_details.phone = ""
                shipping_details.address = type("Address", (), {})()
                shipping_details.address.country = ""
                shipping_details.address.postal_code = ""
                shipping_details.address.city = ""
                shipping_details.address.line1 = ""
                shipping_details.address.line2 = ""
                shipping_details.address.state = ""

            # Debug email after shipping extraction
            # send_mail(
            #     'Test 4 from Zouzou’s Fitness',
            #     f'Shipping details resolved: {shipping_details}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     ['hawraahijazi1996@gmail.com']
            # )

            # Safe extraction of grand total
            if getattr(intent, "charges", None) and getattr(intent.charges, "data", None):
                if intent.charges.data:
                    grand_total = round(intent.charges.data[0].amount / 100, 2)
                else:
                    grand_total = round(getattr(intent, "amount", 0) / 100, 2)
            else:
                grand_total = round(getattr(intent, "amount", 0) / 100, 2)

            # Debug email after grand total extraction
            # send_mail(
            #     'Test 2 from Zouzou’s Fitness',
            #     f'Grand total resolved: {grand_total}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     ['hawraahijazi1996@gmail.com']
            # )

            # Clean empty shipping fields
            for field, value in shipping_details.address.__dict__.items():
                if value == "":
                    setattr(shipping_details.address, field, None)

            # Update user profile if username present
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

            # Look for existing order
            order = None
            order_exists = False
            for attempt in range(10):
                try:
                    order = Order.objects.get(
                        full_name__iexact=shipping_details.name,
                        email__iexact=billing_email,
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

            # Create order if not exists
            if not order_exists:
                order = Order.objects.create(
                    full_name=shipping_details.name,
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
                        continue

            # Debug email before sending confirmation
            # send_mail(
            #     'Test 1 from Zouzou’s Fitness',
            #     'Order and items created successfully. Sending confirmation email.',
            #     settings.DEFAULT_FROM_EMAIL,
            #     ['hawraahijazi1996@gmail.com']
            # )

            self._send_confirmation_email(order)

        except Exception as e:
            # Debug email if anything fails
            send_mail(
                'Test 0 from Zouzou’s Fitness',
                f'Error occurred in webhook: {e}',
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
        """Handle payment_intent.payment_failed webhook from Stripe"""
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
