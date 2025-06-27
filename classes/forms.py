from django import forms
from .models import Booking
from .models import FitnessClass

class FitnessClassForm(forms.ModelForm):
    class Meta:
        model = FitnessClass
        fields = '__all__'

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = []
