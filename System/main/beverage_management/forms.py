from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'first_name', 'last_name', 'phone', 'department', 'password1', 'password2']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'department': forms.TextInput(attrs={'placeholder': 'Department'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set status to pending on registration
        user.status = 'pending'
        # By default, new users should not be active until approved
        user.is_active = False
        
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Email address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['password'].required = True
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username is not None and password:
            # First, try to authenticate with username
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            # If authentication fails, check if username might be an email
            if self.user_cache is None:
                if '@' in username:
                    try:
                        user_obj = User.objects.get(email=username)
                        self.user_cache = authenticate(
                            self.request, 
                            username=user_obj.username, 
                            password=password
                        )
                    except User.DoesNotExist:
                        pass
            
            # If user exists but is not approved, show appropriate message
            if self.user_cache is None:
                # Check if user exists but is not active/approved
                try:
                    user_by_email = User.objects.filter(email=username).first()
                    user_by_username = User.objects.filter(username=username).first()
                    
                    user = user_by_email or user_by_username
                    
                    if user and not user.is_active:
                        raise forms.ValidationError(
                            "Your account is pending approval by administrator.",
                            code='pending_approval',
                        )
                    elif user and user.status == 'rejected':
                        raise forms.ValidationError(
                            "Your account registration has been rejected.",
                            code='account_rejected',
                        )
                    elif user and user.status == 'suspended':
                        raise forms.ValidationError(
                            "Your account has been suspended.",
                            code='account_suspended',
                        )
                except:
                    pass
            
            # If authentication still failed, raise error
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username/email or password",
                    code='invalid_login',
                )
            else:
                # Check if user is approved
                if self.user_cache.status != 'approved':
                    raise forms.ValidationError(
                        "Your account is pending approval by administrator.",
                        code='pending_approval',
                    )
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data