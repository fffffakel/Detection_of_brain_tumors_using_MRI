from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                username = user.username
            except User.DoesNotExist:
                raise forms.ValidationError("This email does not exist.")
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError("This username does not exist.")
        return username