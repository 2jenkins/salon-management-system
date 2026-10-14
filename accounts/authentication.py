from django import forms
from django.contrib.auth.forms import AuthenticationForm

from users.models import CustomUser


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Email or username',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'username',
            'placeholder': 'Enter your email or username',
        }),
    )

    def clean(self):
        identifier = self.cleaned_data.get('username', '').strip()
        if identifier:
            username_exists = CustomUser.objects.filter(username=identifier).exists()
            if not username_exists:
                matches = CustomUser.objects.filter(email__iexact=identifier)
                if matches.count() == 1:
                    self.cleaned_data['username'] = matches.get().get_username()
                elif matches.count() > 1:
                    raise forms.ValidationError(
                        'This email is linked to multiple accounts. Please sign in with your username.'
                    )
            else:
                self.cleaned_data['username'] = identifier

        return super().clean()
