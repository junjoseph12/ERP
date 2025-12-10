from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.template.loader import get_template  
from django.http import HttpResponse            
from xhtml2pdf import pisa
from .models import User, InventoryItem, PurchaseOrder, RequisitionForm, StockAdjustment, Supplier, RequisitionItem, UserActivityLog

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # --- 0. TIME FILTER LOGIC ---
    period = request.GET.get('period', 'monthly') # Default to monthly
    today = timezone.now()
    
    if period == 'daily':
        start_date = today - timedelta(days=1)
        period_label = "Last 24 Hours"
    elif period == 'weekly':
        start_date = today - timedelta(weeks=1)
        period_label = "Last 7 Days"
    elif period == 'annually':
        start_date = today - timedelta(days=365)
        period_label = "Last 365 Days"
    else: # monthly
        start_date = today - timedelta(days=30)
        period_label = "Last 30 Days"

    # --- 1. SYSTEM HEALTH (Global - Not Filtered) ---
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # --- 2. FINANCIALS & SALES (Filtered by Date) ---
    # Sales (Closed Requisitions)
    sales_qs = RequisitionForm.objects.filter(status='closed', date_created__gte=start_date)
    total_sales_count = sales_qs.count()
    
    total_sales_value = RequisitionItem.objects.filter(
        requisition__in=sales_qs
    ).aggregate(
        total=Sum(F('quantity_requested') * F('item__cost_price'))
    )['total'] or 0

    # Purchases (POs Created)
    purchases_qs = PurchaseOrder.objects.filter(date_created__gte=start_date)
    active_pos = purchases_qs.filter(status__in=['ordered', 'in_transit']).count()
    
    # --- 3. DEPARTMENT SEPARATION (Filtered) ---
    # Specific stats for Requesting Party Dept vs Sales Dept vs Others
    req_party_stats = RequisitionForm.objects.filter(
        department='Requesting Party Department', 
        date_created__gte=start_date
    ).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status__in=['pending_dept_head', 'pending_vp'])),
        approved=Count('id', filter=Q(status='approved'))
    )
    
    sales_dept_stats = RequisitionForm.objects.filter(
        department='Sales Department',
        date_created__gte=start_date
    ).aggregate(
        total=Count('id'),
        delivered=Count('id', filter=Q(status='closed'))
    )

    # --- 4. WAREHOUSE (Snapshot) ---
    inventory_value = InventoryItem.objects.aggregate(total=Sum(F('quantity') * F('cost_price')))['total'] or 0
    low_stock_items = InventoryItem.objects.filter(quantity__lte=F('reorder_point')).count()
    out_of_stock_items = InventoryItem.objects.filter(quantity__lte=0).count()
    
    # --- 5. GRAPH DATA ---
    # Line Chart: Transaction Trends (Sales vs POs)
    sales_trend = sales_qs.annotate(date=TruncDate('date_created')).values('date').annotate(c=Count('id')).order_by('date')
    po_trend = purchases_qs.annotate(date=TruncDate('date_created')).values('date').annotate(c=Count('id')).order_by('date')
    
    # Format for Chart.js
    dates = sorted(list(set([x['date'].strftime('%Y-%m-%d') for x in sales_trend] + [x['date'].strftime('%Y-%m-%d') for x in po_trend])))
    
    # Doughnut: Department Share
    dept_share = RequisitionForm.objects.filter(date_created__gte=start_date).values('department').annotate(c=Count('id')).order_by('-c')

    # --- 6. LISTS ---
    recent_stock_moves = StockAdjustment.objects.filter(timestamp__gte=start_date).select_related('item', 'user').order_by('-timestamp')[:5]
    recent_pos = purchases_qs.select_related('supplier').order_by('-date_created')[:5]
    recent_reqs = RequisitionForm.objects.filter(date_created__gte=start_date).select_related('requester').order_by('-date_created')[:5]
    recent_sales = sales_qs.select_related('requester').order_by('-date_created')[:5]

    context = {
        'user': request.user,
        'period': period,
        'period_label': period_label,
        'analytics': {
            'inventory_value': inventory_value,
            'low_stock': low_stock_items,
            'out_of_stock': out_of_stock_items,
            'active_pos': active_pos,
            'total_sales_count': total_sales_count,
            'total_sales_value': total_sales_value,
            'total_suppliers': Supplier.objects.filter(is_active=True).count(),
            # Separated Stats
            'req_party_total': req_party_stats['total'],
            'req_party_pending': req_party_stats['pending'],
            'sales_dept_delivered': sales_dept_stats['delivered']
        },
        'charts': {
            'dates': dates,
            'sales_data': [next((item['c'] for item in sales_trend if item['date'].strftime('%Y-%m-%d') == d), 0) for d in dates],
            'po_data': [next((item['c'] for item in po_trend if item['date'].strftime('%Y-%m-%d') == d), 0) for d in dates],
            'dept_labels': [d['department'] for d in dept_share],
            'dept_data': [d['c'] for d in dept_share],
        },
        'warehouse_data': {'recent_moves': recent_stock_moves},
        'purchasing_data': {'recent_pos': recent_pos},
        'staff_data': {'recent_reqs': recent_reqs},
        'sales_data': {'recent_sales': recent_sales}
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

@login_required
def admin_activity_logs_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')

    # Filter Logic
    query = request.GET.get('q', '')
    date_filter = request.GET.get('date', 'all')
    
    logs_list = UserActivityLog.objects.select_related('user').order_by('-timestamp')

    # Search (User or Action)
    if query:
        logs_list = logs_list.filter(
            Q(user__email__icontains=query) | 
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(action__icontains=query)
        )

    # Date Filter
    today = timezone.now()
    if date_filter == 'today':
        logs_list = logs_list.filter(timestamp__date=today.date())
    elif date_filter == 'week':
        start_date = today - timedelta(days=7)
        logs_list = logs_list.filter(timestamp__gte=start_date)
    elif date_filter == 'month':
        start_date = today - timedelta(days=30)
        logs_list = logs_list.filter(timestamp__gte=start_date)

    # Pagination
    paginator = Paginator(logs_list, 20) # Show 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'System Activity Logs',
        'page_obj': page_obj,
        'query': query,
        'date_filter': date_filter
    }
    return render(request, 'admin/activity_logs.html', context)

@login_required
def admin_export_dashboard_pdf_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # --- 1. COPY LOGIC FROM DASHBOARD VIEW TO GATHER DATA ---
    period = request.GET.get('period', 'monthly') 
    today = timezone.now()
    
    if period == 'daily':
        start_date = today - timedelta(days=1)
        period_label = "Last 24 Hours"
    elif period == 'weekly':
        start_date = today - timedelta(weeks=1)
        period_label = "Last 7 Days"
    elif period == 'annually':
        start_date = today - timedelta(days=365)
        period_label = "Last 365 Days"
    else: 
        start_date = today - timedelta(days=30)
        period_label = "Last 30 Days"

    # Financials
    sales_qs = RequisitionForm.objects.filter(status='closed', date_created__gte=start_date)
    total_sales_count = sales_qs.count()
    
    total_sales_value = RequisitionItem.objects.filter(
        requisition__in=sales_qs
    ).aggregate(
        total=Sum(F('quantity_requested') * F('item__cost_price'))
    )['total'] or 0

    purchases_qs = PurchaseOrder.objects.filter(date_created__gte=start_date)
    active_pos = purchases_qs.filter(status__in=['ordered', 'in_transit']).count()
    
    # Req Party Stats
    req_party_stats = RequisitionForm.objects.filter(
        department='Requesting Party Department', 
        date_created__gte=start_date
    ).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status__in=['pending_dept_head', 'pending_vp'])),
    )
    
    # Inventory Snapshot
    inventory_value = InventoryItem.objects.aggregate(total=Sum(F('quantity') * F('cost_price')))['total'] or 0
    low_stock_items = InventoryItem.objects.filter(quantity__lte=F('reorder_point')).count()
    out_of_stock_items = InventoryItem.objects.filter(quantity__lte=0).count()
    
    # Recent Lists
    recent_pos = purchases_qs.select_related('supplier').order_by('-date_created')[:10]
    recent_sales = sales_qs.select_related('requester').order_by('-date_created')[:10]

    # --- 2. PREPARE CONTEXT ---
    context = {
        'user': request.user,
        'period_label': period_label,
        'generated_at': timezone.now(),
        'analytics': {
            'inventory_value': inventory_value,
            'low_stock': low_stock_items,
            'out_of_stock': out_of_stock_items,
            'active_pos': active_pos,
            'total_sales_count': total_sales_count,
            'total_sales_value': total_sales_value,
            'req_party_total': req_party_stats['total'],
            'req_party_pending': req_party_stats['pending'],
        },
        'purchasing_data': {'recent_pos': recent_pos},
        'sales_data': {'recent_sales': recent_sales}
    }

    # --- 3. GENERATE PDF ---
    template_path = 'admin/dashboard_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    
    # Create Response
    response = HttpResponse(content_type='application/pdf')
    # Use 'attachment' to force download
    filename = f"Admin_Report_{today.strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def admin_export_logs_pdf_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')

    # --- 1. REPLICATE FILTER LOGIC ---
    query = request.GET.get('q', '')
    date_filter = request.GET.get('date', 'all')
    
    logs_list = UserActivityLog.objects.select_related('user').order_by('-timestamp')

    # Apply Search
    if query:
        logs_list = logs_list.filter(
            Q(user__email__icontains=query) | 
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(action__icontains=query)
        )

    # Apply Date Filter
    today = timezone.now()
    if date_filter == 'today':
        logs_list = logs_list.filter(timestamp__date=today.date())
    elif date_filter == 'week':
        start_date = today - timedelta(days=7)
        logs_list = logs_list.filter(timestamp__gte=start_date)
    elif date_filter == 'month':
        start_date = today - timedelta(days=30)
        logs_list = logs_list.filter(timestamp__gte=start_date)

    # Limit for PDF performance (optional, e.g., max 500 rows to prevent timeout)
    # logs_list = logs_list[:500] 

    # --- 2. PREPARE CONTEXT ---
    context = {
        'user': request.user,
        'logs': logs_list,
        'query': query,
        'date_filter': date_filter,
        'generated_at': timezone.now(),
    }

    # --- 3. GENERATE PDF ---
    template_path = 'admin/activity_logs_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Activity_Logs_{today.strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response