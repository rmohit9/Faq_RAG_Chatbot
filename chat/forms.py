from django import forms
from .models import BotConfiguration, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class BotConfigurationForm(forms.ModelForm):
    class Meta:
        model = BotConfiguration
        fields = ['name', 'prompt_template']
        widgets = {
            'prompt_template': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()
            # simple placeholders for better UX
            if field_name == 'name' and 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = 'Enter bot name'
            if field_name == 'prompt_template' and 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = 'Describe bot persona and instructions'

class UserRegistrationForm(UserCreationForm):
    captcha = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter CAPTCHA'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'captcha')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if not self.request or 'captcha_text' not in self.request.session:
            raise forms.ValidationError("CAPTCHA session not found. Please refresh the page.")
        
        if captcha.upper() != self.request.session['captcha_text'].upper():
            raise forms.ValidationError("Incorrect CAPTCHA.")
        return captcha

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(user=user)
        return user


from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User # Import User model

class EmailAuthenticationForm(AuthenticationForm):
    captcha = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter CAPTCHA'}))

    # Remove the default 'username' field from the form
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = forms.EmailField(label="Email", max_length=254) # Add email field

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        captcha = self.cleaned_data.get('captcha')

        if not self.request or 'captcha_text' not in self.request.session:
            raise forms.ValidationError("CAPTCHA session not found. Please refresh the page.")
        
        if captcha.upper() != self.request.session['captcha_text'].upper():
            raise forms.ValidationError("Incorrect CAPTCHA.")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            if user is not None and user.check_password(password):
                self.user_cache = user
            else:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.fields['email'].label},
                )
        return self.cleaned_data
