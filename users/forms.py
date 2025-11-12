from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User,Interest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Row, Column
from django.utils import timezone
from datetime import date

def get_max_dob():
    today = date.today()
    return date(today.year - 18, today.month, today.day)


class UserRegisterForm(UserCreationForm):
    dob = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="You must be 18+"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'dob', 'gender', 'bio', 'profile_photo', 'city', 'password1', 'password2']
        # Removed 'age' — it's calculated from dob!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dob'].widget.attrs['max'] = get_max_dob().isoformat()
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Sign Up', css_class='btn btn-dark w-100 mt-3'))

    def clean_dob(self):
        dob = self.cleaned_data['dob']
        if dob and dob > get_max_dob():
            raise forms.ValidationError("You must be 18 or older.")
        return dob


class UserProfileForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = User
        fields = ['dob', 'gender', 'bio', 'profile_photo', 'city', 'latitude', 'longitude']
        help_texts = {'username': None}
        widgets = {
            'dob': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
            'profile_photo': forms.ClearableFileInput(),
            'city': forms.TextInput(attrs={'placeholder': 'Your city'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DYNAMIC max date: 18 years ago from TODAY
        self.fields['dob'].widget.attrs['max'] = get_max_dob().isoformat()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Changes', css_class='btn btn-dark w-100 mt-3'))

    def clean_dob(self):
        dob = self.cleaned_data['dob']
        if dob and dob > get_max_dob():
            raise forms.ValidationError("You must be 18 or older to use BlindSpark.")
        return dob
    


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('login', 'Login', css_class='btn-primary w-100 mt-3'))

    class Meta:
        model = User
        fields = ['username', 'password']