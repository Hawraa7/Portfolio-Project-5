from django import forms
from .widgets import CustomClearableFileInput
from .models import Product, Category

class ProductForm(forms.ModelForm):
    image = forms.ImageField(
        label='Image',
        required=False,
        widget=CustomClearableFileInput
    )

    SIZE_CHOICES_ALPHA = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]

    SIZE_CHOICES_NUMERIC = [
        (str(i), str(i)) for i in range(36, 48)
    ]

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update category field with friendly names
        categories = Category.objects.all()
        friendly_names = [(c.id, c.get_friendly_name()) for c in categories]
        self.fields['category'].choices = friendly_names

        # Style all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'border-black rounded-0'

        # Add size field conditionally
        instance = kwargs.get('instance', None)

        is_shoe = False
        if instance:
            if instance.category and instance.category.name.lower() == 'shoes':
                is_shoe = True
            elif 'shoe' in instance.name.lower():
                is_shoe = True
        else:
            name = self.data.get('name', '').lower()
            cat_id = self.data.get('category')
            category_name = ''
            if cat_id:
                try:
                    category = Category.objects.get(id=cat_id)
                    category_name = category.name.lower()
                except Category.DoesNotExist:
                    pass
            if 'shoe' in name or category_name == 'shoes':
                is_shoe = True

        if self.instance.has_sizes or self.data.get('has_sizes') == 'on':
            self.fields['size'] = forms.ChoiceField(
                choices=self.SIZE_CHOICES_NUMERIC if is_shoe else self.SIZE_CHOICES_ALPHA,
                label="Size",
                required=True,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
