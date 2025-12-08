from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def purchasing_dashboard_view(request):
    # Check if user is purchasing officer
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    # Mock data for purchasing dashboard based on requirements
    context = {
        'user': request.user,
        'dashboard_title': 'Purchasing Officer Dashboard',
        
        # Main Stats
        'pending_requisitions': 7,
        'active_purchase_orders': 12,
        'awaiting_approval': 3,
        'total_suppliers': 15,
        'high_priority_reqs': 3,
        'po_total_value': '42,500',
        'overdue_approvals': 1,
        'preferred_suppliers': 8,
        'approved_requisitions': 18,
        'processed_today': 5,
        
        # Requisitions Needing Attention
        'requisitions_needing_attention': [
            {
                'id': 'REQ-2024-0015',
                'department': 'Sales Department',
                'urgency': 'High',
                'items': 8,
                'quantity': 45,
                'date': 'Jan 15, 2024'
            },
            {
                'id': 'REQ-2024-0016',
                'department': 'Marketing Department',
                'urgency': 'Medium',
                'items': 5,
                'quantity': 25,
                'date': 'Jan 14, 2024'
            },
            {
                'id': 'REQ-2024-0017',
                'department': 'Office Floor 3',
                'urgency': 'High',
                'items': 3,
                'quantity': 15,
                'date': 'Jan 15, 2024'
            },
        ],
        
        # Supplier List
        'supplier_list': [
            {
                'name': 'Beverage Supply Co.',
                'contact': 'John Smith | (555) 123-4567',
                'rating': 'Excellent',
                'last_order': 'Jan 10, 2024',
                'products': 'Soft Drinks, Energy Drinks',
                'on_time_rate': '98%'
            },
            {
                'name': 'Drinks Distributors',
                'contact': 'Sarah Johnson | (555) 987-6543',
                'rating': 'Good',
                'last_order': 'Jan 12, 2024',
                'products': 'Juices, Water, Sports Drinks',
                'on_time_rate': '92%'
            },
            {
                'name': 'Refreshment Wholesale',
                'contact': 'Mike Wilson | (555) 456-7890',
                'rating': 'Average',
                'last_order': 'Jan 5, 2024',
                'products': 'Alcoholic Beverages, Mixers',
                'on_time_rate': '78%'
            },
            {
                'name': 'Global Beverages',
                'contact': 'Emma Davis | (555) 234-5678',
                'rating': 'Excellent',
                'last_order': 'Jan 8, 2024',
                'products': 'Premium Waters, Specialty Drinks',
                'on_time_rate': '99%'
            },
            {
                'name': 'Premium Drinks Ltd.',
                'contact': 'Robert Brown | (555) 876-5432',
                'rating': 'Good',
                'last_order': 'Jan 13, 2024',
                'products': 'Craft Sodas, Organic Juices',
                'on_time_rate': '95%'
            },
        ],
        
        # Active Purchase Orders
        'active_po_list': [
            {
                'number': 'PO-2024-0012',
                'supplier': 'Beverage Supply Co.',
                'items': 8,
                'quantity': 125,
                'amount': '3,250',
                'status': 'Approved',
                'order_date': 'Jan 10, 2024',
                'eta': 'Jan 15, 2024'
            },
            {
                'number': 'PO-2024-0013',
                'supplier': 'Drinks Distributors',
                'items': 5,
                'quantity': 85,
                'amount': '1,850',
                'status': 'Ordered',
                'order_date': 'Jan 12, 2024',
                'eta': 'Jan 17, 2024'
            },
            {
                'number': 'PO-2024-0014',
                'supplier': 'Refreshment Wholesale',
                'items': 12,
                'quantity': 200,
                'amount': '5,200',
                'status': 'Pending',
                'order_date': 'Jan 14, 2024',
                'eta': 'Jan 20, 2024'
            },
            {
                'number': 'PO-2024-0015',
                'supplier': 'Global Beverages',
                'items': 6,
                'quantity': 95,
                'amount': '2,750',
                'status': 'Shipped',
                'order_date': 'Jan 8, 2024',
                'eta': 'Jan 13, 2024'
            },
            {
                'number': 'PO-2024-0016',
                'supplier': 'Premium Drinks Ltd.',
                'items': 4,
                'quantity': 60,
                'amount': '1,950',
                'status': 'Delivered',
                'order_date': 'Jan 5, 2024',
                'eta': 'Jan 10, 2024'
            },
        ],
        
        # PO Status Summary
        'po_status_summary': {
            'draft': 2,
            'pending': 3,
            'approved': 5,
            'ordered': 4,
            'received': 8
        }
    }
    return render(request, 'purchasing_officer/dashboard.html', context)

@login_required
def purchasing_requisitions_view(request):
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Requisitions Management'
    }
    return render(request, 'purchasing_officer/requisitions.html', context)

@login_required
def purchasing_orders_view(request):
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Purchase Orders'
    }
    return render(request, 'purchasing_officer/orders.html', context)

@login_required
def purchasing_suppliers_view(request):
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Supplier Management'
    }
    return render(request, 'purchasing_officer/suppliers.html', context)

@login_required
def purchasing_create_po_view(request):
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    # Mock data for PO creation
    context = {
        'user': request.user,
        'page_title': 'Create Purchase Order',
        
        # Mock requisitions for selection
        'approved_requisitions': [
            {
                'id': 'REQ-2024-0014',
                'department': 'Marketing Department',
                'date': '2024-01-14',
                'items': 8,
                'quantity': 45,
                'urgency': 'High',
                'total_estimated': '1,250.00'
            },
            {
                'id': 'REQ-2024-0015',
                'department': 'Sales Department',
                'date': '2024-01-15',
                'items': 12,
                'quantity': 65,
                'urgency': 'Medium',
                'total_estimated': '2,850.00'
            },
            {
                'id': 'REQ-2024-0016',
                'department': 'Operations',
                'date': '2024-01-13',
                'items': 5,
                'quantity': 120,
                'urgency': 'High',
                'total_estimated': '1,850.00'
            }
        ],
        
        # Mock suppliers
        'suppliers': [
            {'id': 1, 'name': 'Beverage Supply Co.', 'category': 'Soft Drinks, Energy Drinks', 'rating': '98%'},
            {'id': 2, 'name': 'Drinks Distributors', 'category': 'Juices, Water, Sports Drinks', 'rating': '92%'},
            {'id': 3, 'name': 'Global Beverages', 'category': 'Premium Waters, Specialty Drinks', 'rating': '99%'},
            {'id': 4, 'name': 'Refreshment Wholesale', 'category': 'Alcoholic Beverages, Mixers', 'rating': '78%'},
        ],
        
        # Payment terms
        'payment_terms': [
            {'value': 'net15', 'label': 'Net 15'},
            {'value': 'net30', 'label': 'Net 30'},
            {'value': 'net45', 'label': 'Net 45'},
            {'value': 'net60', 'label': 'Net 60'},
            {'value': 'immediate', 'label': 'Immediate Payment'},
        ],
        
        # Delivery options
        'delivery_options': [
            {'value': 'standard', 'label': 'Standard (3-5 days)'},
            {'value': 'express', 'label': 'Express (1-2 days)'},
            {'value': 'next_day', 'label': 'Next Day'},
            {'value': 'scheduled', 'label': 'Scheduled Delivery'},
        ]
    }
    
    if request.method == 'POST':
        # Process form data here
        po_number = request.POST.get('po_number')
        supplier_id = request.POST.get('supplier')
        requisition_id = request.POST.get('requisition')
        delivery_date = request.POST.get('delivery_date')
        payment_terms = request.POST.get('payment_terms')
        delivery_option = request.POST.get('delivery_option')
        notes = request.POST.get('notes')
        
        # Here you would save to database
        messages.success(request, f'Purchase Order {po_number} created successfully!')
        return redirect('purchasing_orders')
    
    return render(request, 'purchasing_officer/create_po.html', context)

@login_required
def purchasing_add_supplier_view(request):
    if request.user.role != 'purchasing_officer':
        messages.error(request, 'Access denied. Purchasing Officer privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Add New Supplier',
        
        # Supplier categories
        'supplier_categories': [
            'Soft Drinks',
            'Energy Drinks',
            'Juices',
            'Water',
            'Alcoholic Beverages',
            'Sports Drinks',
            'Coffee/Tea',
            'Mixers',
            'Specialty Drinks',
            'Packaging Materials'
        ],
        
        # Supplier types
        'supplier_types': [
            {'value': 'manufacturer', 'label': 'Manufacturer'},
            {'value': 'distributor', 'label': 'Distributor'},
            {'value': 'wholesaler', 'label': 'Wholesaler'},
            {'value': 'retailer', 'label': 'Retailer'},
            {'value': 'importer', 'label': 'Importer'},
        ],
        
        # Payment terms
        'payment_terms': [
            {'value': 'net15', 'label': 'Net 15'},
            {'value': 'net30', 'label': 'Net 30'},
            {'value': 'net45', 'label': 'Net 45'},
            {'value': 'net60', 'label': 'Net 60'},
            {'value': 'prepaid', 'label': 'Prepaid'},
        ],
        
        # Countries
        'countries': [
            'United States',
            'Canada',
            'United Kingdom',
            'Australia',
            'Germany',
            'France',
            'China',
            'Japan',
            'South Korea',
            'Mexico'
        ]
    }
    
    if request.method == 'POST':
        # Process form data here
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        categories = request.POST.getlist('categories')
        supplier_type = request.POST.get('supplier_type')
        payment_terms = request.POST.get('payment_terms')
        
        # Here you would save to database
        messages.success(request, f'Supplier "{name}" added successfully!')
        return redirect('purchasing_suppliers')
    
    return render(request, 'purchasing_officer/add_supplier.html', context)