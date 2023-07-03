from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import transaction
from .models import Customer, Restaurant, User



class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 20px;margin-top: 30px;'}),
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 30px; margin-top: 20px;'}),
    )
    contact = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 10px; margin-top: 20px;'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.is_customer = True
        user.save()
        customer = Customer.objects.create(user=user)
        customer.username = self.cleaned_data.get('username')
        customer.contact = self.cleaned_data.get('contact')
        customer.save()
        return user
    


class RestaurantSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 20px;margin-top: 30px;'}),
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 30px; margin-top: 20px;'}),
    )
    contact = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 10px; margin-top: 20px;'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.is_restaurant = True
        user.save()
        restaurant = Restaurant.objects.create(user=user)
        restaurant.username = self.cleaned_data.get('username')
        restaurant.contact = self.cleaned_data.get('contact')
        restaurant.save()
        return user
    


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'style': 'font-size: 20px; margin-bottom: 20px; margin-top: 20px;'}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'style': 'font-size: 20px; margin-bottom: 10px;  margin-top: 20px;'}),
    )


