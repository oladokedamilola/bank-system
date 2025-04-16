from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate


User = get_user_model()



class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))

    class Meta:
        model = User
        fields = ['email']



from django.contrib.auth.forms import SetPasswordForm

class SetPasswordForm(SetPasswordForm):
    pass  # This uses Django's built-in password validation


class CustomLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
        label="Email",
        error_messages={'required': 'Email is required.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        error_messages={'required': 'Password is required.'}
    )


# forms.py
from django import forms
from django.core.exceptions import ValidationError

class PinForm(forms.Form):
    pin = forms.CharField(max_length=6, min_length=6, widget=forms.PasswordInput, label="Enter 6-Digit PIN")
    confirm_pin = forms.CharField(max_length=6, min_length=6, widget=forms.PasswordInput, label="Confirm PIN")

    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm_pin = cleaned_data.get('confirm_pin')

        if pin != confirm_pin:
            raise ValidationError("PINs do not match.")
        if not pin.isdigit():
            raise ValidationError("PIN should only contain digits.")
        if len(pin) != 6:
            raise ValidationError("PIN should be 6 digits long.")
        return cleaned_data



class EnterPinForm(forms.Form):
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your PIN'}),
        label="PIN",
    )