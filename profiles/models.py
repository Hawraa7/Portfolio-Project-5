from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.utils.crypto import get_random_string
from products.models import Category
import random
from django_countries.fields import CountryField


# --- Utility function to set default deadline one year from now ---
def default_deadline():
   return timezone.now().date() + timedelta(days=365)


# --- User Profile ---
class UserProfile(models.Model):
   """Stores default delivery information for a user."""
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   default_phone_number = models.CharField(max_length=20, null=True, blank=True)
   default_street_address1 = models.CharField(max_length=80, null=True, blank=True)
   default_street_address2 = models.CharField(max_length=80, null=True, blank=True)
   default_town_or_city = models.CharField(max_length=40, null=True, blank=True)
   default_county = models.CharField(max_length=80, null=True, blank=True)
   default_postcode = models.CharField(max_length=20, null=True, blank=True)
   default_country = CountryField(blank_label='Country', null=True, blank=True)


   def __str__(self):
       return self.user.username


# --- Promotion ---
class Promotion(models.Model):
   """Represents a category-based promotion with a validity period."""
   category = models.ForeignKey(
       Category,
       on_delete=models.CASCADE,
       related_name="promotions",
       help_text="Product category associated with this promotion."
   )
   percentage = models.PositiveSmallIntegerField(help_text="Discount percentage (1–100)")
   deadline = models.DateField(default=default_deadline, help_text="Promotion expiration date")
   active = models.BooleanField(default=False, help_text="Is the promotion currently active?")
   validity = models.BooleanField(default=True, help_text="Is the promotion still valid?")


   def __str__(self):
       status = "Active" if self.active else "Inactive"
       valid_text = "Valid" if self.validity else "Expired"
       return f"{self.category.name} - {self.percentage}% ({status}, {valid_text}) until {self.deadline}"


   def check_validity(self):
       """Update validity if the deadline has passed."""
       if timezone.now().date() > self.deadline:
           self.validity = False
           self.save(update_fields=["validity"])
       return self.validity


   def use_promotion(self):
       """Mark promotion as used/invalid."""
       self.validity = False
       self.save(update_fields=["validity"])


# --- Voucher ---
class Voucher(models.Model):
   """Represents a monetary discount voucher."""
   value = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                               help_text="Value of the voucher in euros")
   minimum_purchase = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                          help_text="Minimum purchase to apply voucher")
   deadline = models.DateField(default=default_deadline, help_text="Voucher expiration date")
   active = models.BooleanField(default=False, help_text="Is the voucher active?")
   validity = models.BooleanField(default=True, help_text="Is the voucher still valid?")


   def save(self, *args, **kwargs):
       """Automatically set minimum purchase if not provided."""
       if not self.minimum_purchase:
           self.minimum_purchase = self.value + 5
       super().save(*args, **kwargs)


   def use_voucher(self):
       """Mark voucher as used/invalid."""
       self.validity = False
       self.save(update_fields=["validity"])


   def check_validity(self):
       """Check if voucher has expired."""
       if timezone.now().date() > self.deadline:
           self.validity = False
           self.save(update_fields=["validity"])
       return self.validity


   def __str__(self):
       status = "Active" if self.active else "Inactive"
       valid_text = "Valid" if self.validity else "Expired"
       return f"Voucher €{self.value} (Min purchase: €{self.minimum_purchase}) - {status}, {valid_text}"


# --- Subscription ---
class Subscription(models.Model):
   """Tracks user points, promotions, vouchers, and wallet balance."""
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   number = models.CharField(max_length=12, unique=True, default=get_random_string)
   points = models.PositiveIntegerField(default=0)  # 1€ spent = 1 point
   promotions = models.ManyToManyField(Promotion, blank=True)
   vouchers = models.ManyToManyField(Voucher, blank=True)
   wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


   # --- Membership Levels ---
   def get_membership_level(self):
       """Return membership name, stars, and conversion rate from points to wallet dollars."""
       if self.points < 1000:
           return "Standard", 1, 1
       elif self.points < 2000:
           return "Plus", 2, 2
       elif self.points < 3000:
           return "Premium", 3, 3
       elif self.points < 4000:
           return "Metal", 4, 4
       else:
           return "Ultra", 5, 5


   # --- Points management ---
   def add_points(self, amount_spent):
       """Add points based on euros spent."""
       self.points += int(amount_spent)
       self.save()


   def redeem_points(self, points_to_redeem):
       """Convert points to wallet dollars based on membership level (points are not reduced)."""
       if points_to_redeem <= 0:
           return 0
       _, _, dollars_per_100 = self.get_membership_level()
       redeemable_blocks = points_to_redeem // 100
       redeemed_dollars = redeemable_blocks * dollars_per_100
       self.wallet += redeemed_dollars
       self.save(update_fields=["wallet"])
       return redeemed_dollars


   # --- Promotions ---
   def get_random_promotion(self):
       """Generate a promotion with discount increasing with membership level."""
       membership_name, level, base_discount = self.get_membership_level()
       all_categories = Category.objects.all()
       if not all_categories.exists():
           return None
       random_category = random.choice(list(all_categories))
       deadline = timezone.now().date() + timedelta(days=365)
       promotion = Promotion.objects.create(
           category=random_category,
           percentage=base_discount * 2,  # discount increases with level
           deadline=deadline,
           active=True,
       )
       self.promotions.add(promotion)
       self.save()
       return promotion


   def __str__(self):
       return f"Subscription {self.number} for {self.user.username}"


# --- Signals to create profile and subscription on user creation ---
@receiver(post_save, sender=User)
def create_or_update_user_related(sender, instance, created, **kwargs):
   if created:
       UserProfile.objects.create(user=instance)
       Subscription.objects.create(user=instance)
   else:
       instance.userprofile.save()
       if hasattr(instance, 'subscription'):
           instance.subscription.save()
       else:
           Subscription.objects.create(user=instance)



