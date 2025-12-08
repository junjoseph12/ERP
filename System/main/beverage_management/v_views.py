from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from .models import User

def home(request):
    return render(request, 'login_register/home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # DON'T login the user automatically
            # login(request, user)
            messages.success(request, 'Registration submitted successfully! Your account is pending administrator approval.')
            messages.info(request, 'You will receive an email notification once your account is approved.')
            return redirect('home')  # Redirect to home, not dashboard
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'login_register/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect_to_role_dashboard(request.user.role)
        
    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect_to_role_dashboard(user.role)
        else:
            for error in form.errors.get('__all__', []):
                messages.error(request, error)
            for field in form.errors:
                if field != '__all__':
                    for error in form.errors[field]:
                        messages.error(request, f"{field}: {error}")
    else:
        form = UserLoginForm(request=request)
    
    return render(request, 'login_register/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

def redirect_to_role_dashboard(role):
    """Redirect to the appropriate dashboard based on user role"""
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'warehouse_manager':
        return redirect('warehouse_dashboard')
    elif role == 'purchasing_officer':
        return redirect('purchasing_dashboard')
    elif role == 'staff':
        return redirect('staff_dashboard')
    else:
        return redirect('home')

@login_required
def dashboard_view(request):
    # Check if user is approved
    if not request.user.is_approved:
        messages.error(request, 'Your account is pending approval by administrator.')
        logout(request)
        return redirect('home')
    
    return redirect_to_role_dashboard(request.user.role)