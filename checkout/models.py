import uuid
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.conf import settings
from django_countries.fields import CountryField
from products.models import Product
from profiles.models import UserProfile




class Order(models.Model):
   order_number = models.CharField(max_length=32, null=False, editable=False)
   user_profile = models.ForeignKey(
       UserProfile,
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name='orders'
   )
   full_name = models.CharField(max_length=50, null=False, blank=False)
   email = models.EmailField(max_length=254, null=False, blank=False)
   phone_number = models.CharField(max_length=20, null=False, blank=False)
   country = CountryField(blank_label='Country *', null=False, blank=False)
   postcode = models.CharField(max_length=20, null=True, blank=True)
   town_or_city = models.CharField(max_length=40, null=False, blank=False)
   street_address1 = models.CharField(max_length=80, null=False, blank=False)
   street_address2 = models.CharField(max_length=80, null=True, blank=True)
   county = models.CharField(max_length=80, null=True, blank=True)
   date = models.DateTimeField(auto_now_add=True)
   delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, null=False, default=0)
   order_total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
   loyalty_discount = models.DecimalField(
       max_digits=6, decimal_places=2, null=False, default=Decimal("0.00")
   )  # new field to store loyalty/promotion deduction
   grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
   original_bag = models.TextField(null=False, blank=False, default='')
   stripe_pid = models.CharField(max_length=254, null=False, blank=False, default='')


   def _generate_order_number(self):
       """
       Generate a random, unique order number using UUID
       """
       return uuid.uuid4().hex.upper()


   def update_total(self):
       """
       Update grand total each time a line item is added,
       accounting for delivery costs and loyalty discount.
       """
       self.order_total = self.lineitems.aggregate(Sum('lineitem_total'))['lineitem_total__sum'] or 0
       if self.order_total < settings.FREE_DELIVERY_THRESHOLD:
           self.delivery_cost = self.order_total * settings.STANDARD_DELIVERY_PERCENTAGE / 100
       else:
           self.delivery_cost = 0


       # Grand total now accounts for loyalty discount
       self.loyalty_discount = Decimal(str(self.loyalty_discount or 0))
       self.order_total = Decimal(str(self.order_total or 0))
       self.delivery_cost = Decimal(str(self.delivery_cost or 0))

       self.grand_total = self.order_total - self.loyalty_discount + self.delivery_cost
       if self.grand_total < 0:
           self.grand_total = 0
       self.save()


   def save(self, *args, **kwargs):
       """
       Override save to assign order number if not set.
       """
       if not self.order_number:
           self.order_number = self._generate_order_number()
       super().save(*args, **kwargs)


   def __str__(self):
       return self.order_number




class OrderLineItem(models.Model):
   order = models.ForeignKey(
       Order,
       null=False,
       blank=False,
       on_delete=models.CASCADE,
       related_name='lineitems'
   )
   product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.CASCADE)
   product_size = models.CharField(max_length=2, null=True, blank=True)  # XS, S, M, L, XL
   quantity = models.IntegerField(null=False, blank=False, default=0)
   lineitem_total = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, editable=False)


   def save(self, *args, **kwargs):
       """
       Override save to set lineitem total and update order total.
       """
       self.lineitem_total = self.product.price * self.quantity
       super().save(*args, **kwargs)
       # Automatically update the parent order total whenever a line item changes
       self.order.update_total()


   def __str__(self):
       return f'SKU {self.product.sku} on order {self.order.order_number}'