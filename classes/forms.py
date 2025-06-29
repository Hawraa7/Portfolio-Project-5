from django import forms
from .models import FitnessClass, Booking

class FitnessClassForm(forms.ModelForm):
    class Meta:
        model = FitnessClass
        fields = [
            'title', 
            'description', 
            'instructor', 
            'date', 
            'time', 
            'max_participants', 
            'price'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [] 