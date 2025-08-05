from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'available']





from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['hotel', 'name']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-0 shadow-sm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-0 shadow-sm',
                'rows': 3
            }),
        }