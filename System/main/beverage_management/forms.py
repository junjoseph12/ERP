from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, InventoryItem, StockAdjustment, Supplier, PurchaseOrder, RequisitionForm, ReceivingReport

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

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Remove 'admin' from the role choices
        self.fields['role'].choices = [
            (role, label) for role, label in User.ROLE_CHOICES if role != 'admin'
        ]
    
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
    
class InventoryItemForm(forms.ModelForm):
    # 1. Create a new dropdown field that loads Suppliers from the DB
    supplier_select = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True), # Only show active suppliers
        required=False,
        label="Supplier",
        empty_label="Select a Supplier",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = InventoryItem
        # 2. Exclude the original text field so it doesn't conflict
        exclude = ['supplier_name', 'created_at', 'updated_at'] 
        
        # Add styling to other fields to match your design
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BEV-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aisle-Shelf-Bin'}),
        }

    def save(self, commit=True):
        # 3. Override save to grab the name from the dropdown and put it in the text field
        instance = super().save(commit=False)
        
        if self.cleaned_data.get('supplier_select'):
            # Copy the name of the selected supplier object to the supplier_name field
            instance.supplier_name = self.cleaned_data['supplier_select'].name
            
        if commit:
            instance.save()
        return instance

class StockUpdateForm(forms.Form):
    ADJUSTMENT_CHOICES = (
        ('receive', 'Receiving (Add Stock)'),
        ('adjust', 'Manual Adjustment (+/-)'),
        ('damage', 'Damage/Wastage (Remove Stock)'),
        ('set', 'Set Exact Quantity'),
    )
    
    adjustment_type = forms.ChoiceField(choices=ADJUSTMENT_CHOICES, widget=forms.RadioSelect)
    quantity = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    reference = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PO-2024-001'}))
    reason = forms.CharField(required=True, widget=forms.Select(choices=[
        ('Delivery Received', 'Delivery Received'),
        ('Inventory Correction', 'Inventory Correction'),
        ('Damaged Goods', 'Damaged Goods'),
        ('Expired Goods', 'Expired Goods'),
        ('Other', 'Other'),
    ], attrs={'class': 'form-control'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'requisition', 'selection_justification']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'requisition': forms.Select(attrs={'class': 'form-control'}),
            'selection_justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Selected based on lowest price from 3 physical quotes.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter requisitions to only show those needing purchasing
        self.fields['requisition'].queryset = RequisitionForm.objects.filter(
            route_destination='purchasing'
        ).exclude(status='closed')

class ReceivingForm(forms.ModelForm):
    class Meta:
        model = ReceivingReport
        fields = ['delivery_receipt_no', 'inspection_notes', 'quality_check_passed']
        widgets = {
            'delivery_receipt_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Supplier DR #'}),
            'inspection_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Note any damages or expiry issues...'}),
            'quality_check_passed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }