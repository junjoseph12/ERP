from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def staff_dashboard_view(request):
    # Check if user is staff
    if request.user.role != 'staff':
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('home')
    
    # Mock data for staff dashboard
    context = {
        'user': request.user,
        'dashboard_title': 'Staff Dashboard',
        
        # Main Stats
        'available_beverages': 156,
        'my_requisitions': 8,
        'pending_approvals': 2,
        'categories': 8,
        'awaiting_delivery': 3,
        'department_requests': 15,
        'success_rate': '85%',
        'approved_requisitions': 5,
        'pending_requisitions': 2,
        'delivered_requisitions': 3,
        'rejected_requisitions': 0,
        
        # Recent Requisitions
        'recent_requisitions': [
            {
                'id': 'REQ-001',
                'status': 'Approved',
                'items': 5,
                'quantity': 25,
                'date': 'Jan 10'
            },
            {
                'id': 'REQ-002',
                'status': 'Pending',
                'items': 3,
                'quantity': 15,
                'date': 'Jan 12'
            },
            {
                'id': 'REQ-003',
                'status': 'Delivered',
                'items': 8,
                'quantity': 40,
                'date': 'Jan 5'
            },
            {
                'id': 'REQ-004',
                'status': 'Approved',
                'items': 4,
                'quantity': 20,
                'date': 'Jan 8'
            },
            {
                'id': 'REQ-005',
                'status': 'Pending',
                'items': 6,
                'quantity': 30,
                'date': 'Jan 14'
            },
        ],
        
        # Inventory Alerts
        'inventory_alerts': [
            {
                'item': 'Coca-Cola 330ml',
                'category': 'Soft Drinks',
                'status': 'Low Stock',
                'stock': 12
            },
            {
                'item': 'Red Bull 250ml',
                'category': 'Energy Drinks',
                'status': 'Available',
                'stock': 45
            },
            {
                'item': 'Mineral Water 500ml',
                'category': 'Water',
                'status': 'Out of Stock',
                'stock': 0
            },
            {
                'item': 'Orange Juice 1L',
                'category': 'Juices',
                'status': 'Available',
                'stock': 65
            },
            {
                'item': 'Pepsi 500ml',
                'category': 'Soft Drinks',
                'status': 'Low Stock',
                'stock': 8
            },
        ],
        
        # Popular Beverages
        'popular_beverages': [
            {
                'name': 'Coca-Cola',
                'category': 'Soft Drinks',
                'stock': 45
            },
            {
                'name': 'Red Bull',
                'category': 'Energy Drinks',
                'stock': 85
            },
            {
                'name': 'Orange Juice',
                'category': 'Juices',
                'stock': 65
            },
            {
                'name': 'Mineral Water',
                'category': 'Water',
                'stock': 120
            },
            {
                'name': 'Sprite',
                'category': 'Soft Drinks',
                'stock': 35
            },
            {
                'name': 'Gatorade',
                'category': 'Sports Drinks',
                'stock': 55
            },
        ]
    }
    return render(request, 'staff/dashboard.html', context)

@login_required
def staff_inventory_view(request):
    if request.user.role != 'staff':
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'View Inventory'
    }
    return render(request, 'staff/inventory.html', context)

@login_required
def staff_requisition_view(request):
    if request.user.role != 'staff':
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Submit Requisition'
    }
    return render(request, 'staff/submit_requisition.html', context)

@login_required
def staff_my_requisitions_view(request):
    if request.user.role != 'staff':
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'My Requisitions'
    }
    return render(request, 'staff/my_requisitions.html', context)