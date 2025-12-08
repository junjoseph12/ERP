from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def warehouse_dashboard_view(request):
    # Check if user is warehouse manager
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    # Mock data for warehouse dashboard based on requirements
    context = {
        'user': request.user,
        'dashboard_title': 'Warehouse Manager Dashboard',
        
        # Current Stock Levels
        'current_stock_levels': {
            'total_items': 450,
            'in_stock': 420,
            'low_stock': 15,
            'out_of_stock': 3,
            'categories': 8
        },
        
        # Stock by Category
        'stock_by_category': [
            {'name': 'Soft Drinks', 'count': 120, 'percentage': 75, 'color': '#0984e3'},
            {'name': 'Energy Drinks', 'count': 85, 'percentage': 60, 'color': '#00b894'},
            {'name': 'Juices', 'count': 65, 'percentage': 45, 'color': '#e17055'},
            {'name': 'Water', 'count': 95, 'percentage': 70, 'color': '#6c5ce7'},
            {'name': 'Alcoholic', 'count': 35, 'percentage': 25, 'color': '#a29bfe'},
            {'name': 'Coffee/Tea', 'count': 50, 'percentage': 35, 'color': '#fd79a8'},
        ],
        
        'stock_health_percentage': '85%',
        
        # Incoming Deliveries
        'incoming_deliveries': [
            {
                'supplier': 'Beverage Supply Co.',
                'po_number': '2024-0012',
                'items': 5,
                'quantity': 125,
                'expected_date': 'Today, 2:00 PM',
                'status': 'SCHEDULED'
            },
            {
                'supplier': 'Drinks Distributors',
                'po_number': '2024-0013',
                'items': 3,
                'quantity': 85,
                'expected_date': 'Tomorrow, 10:00 AM',
                'status': 'IN TRANSIT'
            },
            {
                'supplier': 'Refreshment Wholesale',
                'po_number': '2024-0014',
                'items': 7,
                'quantity': 200,
                'expected_date': 'Jan 18, 9:00 AM',
                'status': 'SCHEDULED'
            },
            {
                'supplier': 'Global Beverages',
                'po_number': '2024-0015',
                'items': 4,
                'quantity': 95,
                'expected_date': 'Jan 19, 11:00 AM',
                'status': 'CONFIRMED'
            },
        ],
        
        'incoming_items_total': 505,
        
        # Outgoing Shipments
        'outgoing_shipments': [
            {
                'id': 'SHIP-001',
                'destination': 'Sales Department',
                'items_count': 12,
                'total_quantity': 50,
                'status': 'Ready',
                'scheduled_time': 'Today, 3:00 PM'
            },
            {
                'id': 'SHIP-002',
                'destination': 'Marketing Department',
                'items_count': 8,
                'total_quantity': 30,
                'status': 'Packed',
                'scheduled_time': 'Tomorrow, 10:00 AM'
            },
            {
                'id': 'SHIP-003',
                'destination': 'Office Floor 3',
                'items_count': 5,
                'total_quantity': 15,
                'status': 'In Progress',
                'scheduled_time': 'Today, 4:30 PM'
            },
            {
                'id': 'SHIP-004',
                'destination': 'Executive Lounge',
                'items_count': 3,
                'total_quantity': 10,
                'status': 'Packed',
                'scheduled_time': 'Today, 2:00 PM'
            },
            {
                'id': 'SHIP-005',
                'destination': 'Conference Room A',
                'items_count': 6,
                'total_quantity': 25,
                'status': 'Ready',
                'scheduled_time': 'Tomorrow, 8:00 AM'
            },
        ],
        
        'outgoing_items_total': 130,
        
        # Warehouse Space Utilization
        'warehouse_space': {
            'utilization': '75%',
            'utilization_percentage': 0.75,
            'occupied': 1500,
            'available': 500,
            'total': 2000,
            'pallets': 450
        },
        
        # Low Stock Items
        'low_stock_items': [
            {'name': 'Coca-Cola 330ml', 'sku': 'BEV-001', 'current': 12, 'reorder': 50},
            {'name': 'Red Bull 250ml', 'sku': 'BEV-015', 'current': 15, 'reorder': 40},
            {'name': 'Mineral Water 500ml', 'sku': 'BEV-020', 'current': 20, 'reorder': 100},
        ]
    }
    return render(request, 'warehouse_manager/dashboard.html', context)

@login_required
def warehouse_add_item_view(request):
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    if request.method == 'POST':
        # Process form data here
        sku = request.POST.get('sku')
        name = request.POST.get('name')
        description = request.POST.get('description')
        brand = request.POST.get('brand')
        category = request.POST.get('category')
        unit = request.POST.get('unit')
        quantity = request.POST.get('quantity')
        reorder_point = request.POST.get('reorder_point')
        cost_price = request.POST.get('cost_price')
        selling_price = request.POST.get('selling_price')
        expiry_date = request.POST.get('expiry_date')
        location = request.POST.get('location')
        supplier = request.POST.get('supplier')
        
        # Here you would normally save to database
        # For now, we'll just show a success message
        messages.success(request, f'Item "{name}" added successfully!')
        return redirect('warehouse_inventory')
    
    context = {
        'user': request.user,
        'page_title': 'Add New Item'
    }
    return render(request, 'warehouse_manager/add_item.html', context)

@login_required
def warehouse_inventory_view(request):
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    # Mock data for inventory page
    context = {
        'user': request.user,
        'page_title': 'Inventory Management',
        
        # Inventory stats
        'inventory_stats': {
            'total_items': 450,
            'in_stock': 420,
            'low_stock': 15,
            'out_of_stock': 3
        },
        
        # Mock inventory items data
        'inventory_items': [
            {
                'id': 1,
                'sku': 'BEV-001',
                'name': 'Coca-Cola 330ml',
                'description': 'Carbonated soft drink',
                'category': 'Soft Drinks',
                'brand': 'Coca-Cola',
                'quantity': 125,
                'reorder_point': 20,
                'location': 'A1-25'
            },
            {
                'id': 2,
                'sku': 'BEV-002',
                'name': 'Pepsi 500ml',
                'description': 'Carbonated soft drink',
                'category': 'Soft Drinks',
                'brand': 'PepsiCo',
                'quantity': 8,
                'reorder_point': 15,
                'location': 'A1-26'
            },
            {
                'id': 3,
                'sku': 'BEV-015',
                'name': 'Red Bull 250ml',
                'description': 'Energy drink',
                'category': 'Energy Drinks',
                'brand': 'Red Bull',
                'quantity': 15,
                'reorder_point': 10,
                'location': 'B1-10'
            },
            {
                'id': 4,
                'sku': 'BEV-023',
                'name': 'Tropicana Orange Juice 1L',
                'description': '100% pure orange juice',
                'category': 'Juices',
                'brand': 'Tropicana',
                'quantity': 0,
                'reorder_point': 12,
                'location': 'C1-15'
            },
            {
                'id': 5,
                'sku': 'BEV-034',
                'name': 'Evian Natural Water 500ml',
                'description': 'Natural spring water',
                'category': 'Water',
                'brand': 'Evian',
                'quantity': 95,
                'reorder_point': 25,
                'location': 'B2-05'
            }
        ],
        
        # Mock pagination data
        'page_obj': {
            'start_index': 1,
            'end_index': 5,
            'paginator': {
                'count': 450
            },
            'has_other_pages': True,
            'has_previous': False,
            'has_next': True,
            'previous_page_number': None,
            'next_page_number': 2,
            'number': 1,
            'paginator': {
                'page_range': [1, 2, 3, 4, 5]
            }
        },
        
        # Mock alerts
        'inventory_alerts': [
            {
                'message': 'Pepsi 500ml - Low Stock',
                'details': 'Only 8 units remaining'
            },
            {
                'message': 'Tropicana Orange Juice - Out of Stock',
                'details': '0 units remaining'
            },
            {
                'message': 'Red Bull 250ml - Low Stock',
                'details': 'Only 15 units remaining'
            }
        ]
    }
    
    return render(request, 'warehouse_manager/inventory.html', context)

@login_required
def warehouse_receiving_view(request):
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Receiving Management',
        'receiving_stats': {
            'pending': 5,
            'processed': 12,
            'scheduled': 3,
            'items_received': 125
        }
    }
    return render(request, 'warehouse_manager/receiving.html', context)

@login_required
def warehouse_update_stock_view(request, item_id):
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    # Mock item data for now - in real app, you'd fetch from database
    item = {
        'id': item_id,
        'sku': 'BEV-001',
        'name': 'Coca-Cola 330ml',
        'quantity': 125,
        'reorder_point': 20,
        'unit': 'bottles'
    }
    
    if request.method == 'POST':
        # Process stock adjustment
        adjustment_type = request.POST.get('adjustment_type')
        quantity = request.POST.get('quantity')
        reference = request.POST.get('reference')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes')
        
        # Here you would update the database
        messages.success(request, f'Stock updated successfully! Adjustment type: {adjustment_type}, Quantity: {quantity}')
        return redirect('warehouse_manager/inventory')
    
    # Mock recent adjustments
    recent_adjustments = [
        {
            'date': '2024-01-15',
            'type': 'receive',
            'quantity': 25,
            'reason': 'Delivery Received',
            'reference': 'PO-2024-001',
            'user': 'warehouse@company.com'
        },
        {
            'date': '2024-01-10',
            'type': 'damage',
            'quantity': -5,
            'reason': 'Damaged Goods',
            'reference': 'DMG-001',
            'user': 'warehouse@company.com'
        },
        {
            'date': '2024-01-05',
            'type': 'adjust',
            'quantity': 10,
            'reason': 'Inventory Correction',
            'reference': 'CORR-001',
            'user': 'warehouse@company.com'
        },
    ]
    
    context = {
        'user': request.user,
        'page_title': 'Update Stock',
        'item': item,
        'recent_adjustments': recent_adjustments
    }
    return render(request, 'warehouse_manager/update_stock.html', context)

@login_required
def warehouse_new_receiving_view(request):
    if request.user.role != 'warehouse_manager':
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    # Mock data for new receiving form
    context = {
        'user': request.user,
        'page_title': 'New Receiving',
        
        # Mock pending POs for selection
        'pending_purchase_orders': [
            {
                'id': 1,
                'po_number': 'PO-2024-0016',
                'supplier': 'Beverage Express Inc.',
                'order_date': '2024-01-14',
                'expected_delivery': '2024-01-16',
                'total_items': 8,
                'total_quantity': 150,
                'status': 'PENDING'
            },
            {
                'id': 2,
                'po_number': 'PO-2024-0017',
                'supplier': 'Drink Masters Ltd.',
                'order_date': '2024-01-13',
                'expected_delivery': '2024-01-15',
                'total_items': 5,
                'total_quantity': 75,
                'status': 'IN_TRANSIT'
            },
            {
                'id': 3,
                'po_number': 'PO-2024-0018',
                'supplier': 'Refreshment Suppliers',
                'order_date': '2024-01-12',
                'expected_delivery': 'Today',
                'total_items': 12,
                'total_quantity': 200,
                'status': 'SCHEDULED'
            }
        ],
        
        # Mock supplier list
        'suppliers': [
            {'id': 1, 'name': 'Beverage Supply Co.', 'contact': 'John Smith'},
            {'id': 2, 'name': 'Drinks Distributors', 'contact': 'Sarah Johnson'},
            {'id': 3, 'name': 'Refreshment Wholesale', 'contact': 'Mike Wilson'},
            {'id': 4, 'name': 'Global Beverages', 'contact': 'Emily Chen'},
            {'id': 5, 'name': 'Beverage Express Inc.', 'contact': 'David Lee'},
            {'id': 6, 'name': 'Drink Masters Ltd.', 'contact': 'Lisa Wang'},
        ],
        
        # Mock delivery status options
        'delivery_statuses': [
            {'value': 'scheduled', 'label': 'Scheduled'},
            {'value': 'in_transit', 'label': 'In Transit'},
            {'value': 'arrived', 'label': 'Arrived'},
            {'value': 'unloading', 'label': 'Unloading'},
            {'value': 'inspecting', 'label': 'Quality Inspection'},
            {'value': 'complete', 'label': 'Complete'},
            {'value': 'partial', 'label': 'Partial Delivery'},
        ],
        
        # Mock quality check options
        'quality_checks': [
            {'value': 'good', 'label': 'Good', 'color': '#00b894'},
            {'value': 'damaged', 'label': 'Damaged', 'color': '#ff6b6b'},
            {'value': 'expired', 'label': 'Expired', 'color': '#fdcb6e'},
            {'value': 'wrong_item', 'label': 'Wrong Item', 'color': '#0984e3'},
        ]
    }
    
    if request.method == 'POST':
        # Process the form data here
        po_number = request.POST.get('po_number')
        delivery_date = request.POST.get('delivery_date')
        carrier = request.POST.get('carrier')
        tracking_number = request.POST.get('tracking_number')
        delivery_status = request.POST.get('delivery_status')
        notes = request.POST.get('notes')
        
        # Here you would save to database
        messages.success(request, f'New receiving record created for {po_number}')
        return redirect('warehouse_receiving')
    
    return render(request, 'warehouse_manager/new_receiving.html', context)