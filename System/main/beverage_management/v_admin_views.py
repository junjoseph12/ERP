from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.core.paginator import Paginator
from .models import User, InventoryItem, PurchaseOrder, RequisitionForm, StockAdjustment, Supplier, RequisitionItem

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # --- 1. SYSTEM HEALTH (Global) ---
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # --- 2. WAREHOUSE MODULE ANALYTICS ---
    inventory_value = InventoryItem.objects.aggregate(total=Sum(F('quantity') * F('cost_price')))['total'] or 0
    low_stock_items = InventoryItem.objects.filter(quantity__lte=F('reorder_point')).count()
    out_of_stock_items = InventoryItem.objects.filter(quantity__lte=0).count()
    recent_stock_moves = StockAdjustment.objects.select_related('item', 'user').order_by('-timestamp')[:5]

    # --- 3. PURCHASING MODULE ANALYTICS ---
    active_pos = PurchaseOrder.objects.filter(status__in=['ordered', 'in_transit']).count()
    completed_pos = PurchaseOrder.objects.filter(status='completed').count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    recent_pos = PurchaseOrder.objects.select_related('supplier').order_by('-date_created')[:5]

    # --- 4. STAFF/REQUISITION MODULE ANALYTICS ---
    pending_reqs = RequisitionForm.objects.filter(status__in=['pending_dept_head', 'pending_vp']).count()
    approved_reqs = RequisitionForm.objects.filter(status='approved').count()
    recent_reqs = RequisitionForm.objects.filter(status__in=['pending_dept_head', 'pending_vp', 'approved']).select_related('requester').order_by('-date_created')[:5]
    
    # --- 5. SALES ANALYTICS (Closed Requisitions) ---
    total_sales_count = RequisitionForm.objects.filter(status='closed').count()
    
    # Calculate Total Sales Value (Sum of quantity * cost_price for items in closed requisitions)
    total_sales_value = RequisitionItem.objects.filter(requisition__status='closed').aggregate(
        total=Sum(F('quantity_requested') * F('item__cost_price'))
    )['total'] or 0
    
    # Recent Sales List
    recent_sales = RequisitionForm.objects.filter(status='closed').select_related('requester').order_by('-date_created')[:5]

    # --- 6. DEPARTMENT USAGE ---
    dept_usage = RequisitionForm.objects.values('department').annotate(request_count=Count('id')).order_by('-request_count')[:5]

    context = {
        'user': request.user,
        'analytics': {
            'inventory_value': inventory_value,
            'low_stock': low_stock_items,
            'out_of_stock': out_of_stock_items,
            'active_pos': active_pos,
            'completed_pos': completed_pos,
            'total_suppliers': total_suppliers,
            'pending_reqs': pending_reqs,
            'approved_reqs': approved_reqs,
            'total_users': total_users,
            'active_users': active_users,
            # New Sales Stats
            'total_sales_count': total_sales_count,
            'total_sales_value': total_sales_value
        },
        'warehouse_data': {
            'recent_moves': recent_stock_moves
        },
        'purchasing_data': {
            'recent_pos': recent_pos
        },
        'staff_data': {
            'recent_reqs': recent_reqs,
            'dept_usage': dept_usage
        },
        'sales_data': {
            'recent_sales': recent_sales
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

@login_required
def admin_edit_user_view(request, user_id):
    # Security check
    if request.user.role != 'admin' or not request.user.is_approved:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update standard fields
        user_to_edit.first_name = request.POST.get('first_name', user_to_edit.first_name)
        user_to_edit.last_name = request.POST.get('last_name', user_to_edit.last_name)
        user_to_edit.email = request.POST.get('email', user_to_edit.email)
        
        # Update custom fields
        user_to_edit.phone = request.POST.get('phone', user_to_edit.phone)
        user_to_edit.department = request.POST.get('department', user_to_edit.department)
        user_to_edit.role = request.POST.get('role', user_to_edit.role)
        
        # --- ADDED: Update Status ---
        user_to_edit.status = request.POST.get('status', user_to_edit.status)
        
        # Logic: If status is approved, ensure is_active is True, else False (unless pending)
        if user_to_edit.status == 'approved':
            user_to_edit.is_active = True
        elif user_to_edit.status in ['rejected', 'suspended']:
            user_to_edit.is_active = False
            
        user_to_edit.save()
        
        messages.success(request, f'Profile for {user_to_edit.email} has been updated.')
        
    return redirect('admin_user_detail', user_id=user_id)