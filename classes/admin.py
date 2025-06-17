from django.contrib import admin
from .models import FitnessClass, Booking

@admin.register(FitnessClass)
class FitnessClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'instructor', 'max_participants')
    list_filter = ('instructor', 'date')

admin.site.register(Booking)

