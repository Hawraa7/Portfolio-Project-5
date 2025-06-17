from django import forms
from .models import FitnessClass

class FitnessClassForm(forms.ModelForm):
    class Meta:
        model = FitnessClass
        fields = ['title', 'description', 'date', 'time', 'instructor', 'max_participants']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
