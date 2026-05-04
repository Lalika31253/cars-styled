# showroom/forms.py
from django import forms
from .models import Car, Seller
# Authentication
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CarForm(forms.ModelForm):
    class Meta:
        model  = Car
        fields = ['make', 'model', 'year', 'price',
                  'transmission', 'branch', 'seller']


class SellerForm(forms.ModelForm):
    class Meta:
        model  = Seller
        fields = ['first_name', 'last_name', 'branches', 'is_active']

# Authentication
class RegisterForm(UserCreationForm):
    # email is optional — remove if you don't need it
    email = forms.EmailField(required=False)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']