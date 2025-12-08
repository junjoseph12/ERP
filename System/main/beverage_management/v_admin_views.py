from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import User  # Adjust the import path based on your project structure

@login_required
def admin_dashboard_view(request):
    # Check if user is admin
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # Mock data for admin dashboard based on requirements
    context = {
        'user': request.user,
        'total_inventory_value': 125847,
        'low_stock_alerts': 12,
        'pending_purchase_orders': 8,
        'delivery_status_overview': {
            'delivered': 24,
            'in_transit': 4,
            'pending': 2,
            'delayed': 0,
            'total': 30
        },
        'recent_audit_logs': [
            {
                'timestamp': '2024-01-15 14:30',
                'user': 'admin@company.com',
                'action_type': 'update',
                'module': 'Inventory',
                'details': 'Updated stock quantity for Coca-Cola 330ml',
                'ip': '192.168.1.100'
            },
            {
                'timestamp': '2024-01-15 10:15',
                'user': 'warehouse@company.com',
                'action_type': 'create',
                'module': 'Purchase',
                'details': 'Created new purchase order #PO-2024-001',
                'ip': '192.168.1.101'
            },
            {
                'timestamp': '2024-01-14 16:45',
                'user': 'purchasing@company.com',
                'action_type': 'login',
                'module': 'System',
                'details': 'User logged in from new device',
                'ip': '192.168.1.102'
            },
            {
                'timestamp': '2024-01-14 09:20',
                'user': 'staff@company.com',
                'action_type': 'create',
                'module': 'Requisition',
                'details': 'Submitted new beverage requisition',
                'ip': '192.168.1.103'
            },
            {
                'timestamp': '2024-01-13 11:00',
                'user': 'admin@company.com',
                'action_type': 'create',
                'module': 'Users',
                'details': 'Added new user: warehouse@company.com',
                'ip': '192.168.1.100'
            },
        ],
        'low_stock_items': [
            {'name': 'Coca-Cola 330ml', 'sku': 'BEV-001', 'stock': 12},
            {'name': 'Pepsi 500ml', 'sku': 'BEV-002', 'stock': 8},
            {'name': 'Red Bull 250ml', 'sku': 'BEV-015', 'stock': 15},
            {'name': 'Sprite 1L', 'sku': 'BEV-003', 'stock': 10},
            {'name': 'Mineral Water 500ml', 'sku': 'BEV-020', 'stock': 20},
        ],
        'pending_po_list': [
            {'number': 'PO-2024-001', 'supplier': 'Beverage Supply Co.', 'amount': '3,250', 'status': 'Pending'},
            {'number': 'PO-2024-002', 'supplier': 'Drinks Distributors', 'amount': '5,800', 'status': 'Approved'},
            {'number': 'PO-2024-003', 'supplier': 'Refreshment Wholesale', 'amount': '2,150', 'status': 'Pending'},
            {'number': 'PO-2024-004', 'supplier': 'Global Beverages', 'amount': '4,750', 'status': 'Pending'},
            {'number': 'PO-2024-005', 'supplier': 'Premium Drinks Ltd.', 'amount': '6,200', 'status': 'Approved'},
        ],
        'quick_stats': {
            'total_users': 24,
            'active_suppliers': 12,
            'total_products': 156,
            'monthly_orders': 48
        }
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def admin_user_management_view(request):
    # Check if user is admin
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # Get filter parameter
    status_filter = request.GET.get('status', 'pending')
    
    # Filter users based on status
    if status_filter == 'all':
        users = User.objects.all().order_by('-date_joined')
    elif status_filter == 'approved':
        users = User.objects.filter(status='approved').order_by('-date_joined')
    elif status_filter == 'pending':
        users = User.objects.filter(status='pending').order_by('-date_joined')
    elif status_filter == 'rejected':
        users = User.objects.filter(status='rejected').order_by('-date_joined')
    else:
        users = User.objects.filter(status='pending').order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'page_title': 'User Management',
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_users': User.objects.count(),
        'pending_users': User.objects.filter(status='pending').count(),
        'approved_users': User.objects.filter(status='approved').count(),
        'rejected_users': User.objects.filter(status='rejected').count(),
    }
    return render(request, 'admin/user_management.html', context)

@login_required
def admin_approve_user_view(request, user_id):
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_to_approve = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user_to_approve.status = 'approved'
        user_to_approve.is_active = True
        user_to_approve.save()
        
        messages.success(request, f'User {user_to_approve.email} has been approved.')
        
        # Here you could send an email notification to the user
        # send_approval_email(user_to_approve)
        
    return redirect('admin_users')

@login_required
def admin_reject_user_view(request, user_id):
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_to_reject = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')
        user_to_reject.status = 'rejected'
        user_to_reject.is_active = False
        user_to_reject.save()
        
        messages.success(request, f'User {user_to_reject.email} has been rejected.')
        
        # Here you could send a rejection email with the reason
        # send_rejection_email(user_to_reject, reason)
        
    return redirect('admin_users')

@login_required
def admin_suspend_user_view(request, user_id):
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_to_suspend = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')
        user_to_suspend.status = 'suspended'
        user_to_suspend.is_active = False
        user_to_suspend.save()
        
        messages.success(request, f'User {user_to_suspend.email} has been suspended.')
        
    return redirect('admin_users')

@login_required
def admin_reactivate_user_view(request, user_id):
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_to_reactivate = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user_to_reactivate.status = 'approved'
        user_to_reactivate.is_active = True
        user_to_reactivate.save()
        
        messages.success(request, f'User {user_to_reactivate.email} has been reactivated.')
        
    return redirect('admin_users')

@login_required
def admin_user_detail_view(request, user_id):
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_detail = get_object_or_404(User, id=user_id)
    
    context = {
        'user': request.user,
        'user_detail': user_detail,
        'page_title': f'User Details - {user_detail.email}'
    }
    return render(request, 'admin/user_detail.html', context)

@login_required
def admin_system_settings_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'System Settings'
    }
    return render(request, 'admin/system_settings.html', context)