from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Sum, Count
from django.utils import timezone

from .models import InventoryItem, StockAdjustment, ReceivingReport, InternalDelivery
from .forms import InventoryItemForm, StockUpdateForm

# ==========================================
# 1. DASHBOARD
# ==========================================
@login_required
def warehouse_dashboard_view(request):
    if request.user.role != 'warehouse_manager' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Warehouse Manager privileges required.')
        return redirect('home')
    
    # Real DB Stats
    total_items = InventoryItem.objects.count()
    # Filter items where quantity < reorder_point
    low_stock_count = InventoryItem.objects.filter(quantity__lte=F('reorder_point')).count()
    out_of_stock_count = InventoryItem.objects.filter(quantity__lte=0).count()
    in_stock_count = total_items - (low_stock_count + out_of_stock_count) # Simplified logic
    
    # Calculate stock by category for the chart
    stock_by_category = InventoryItem.objects.values('category').annotate(count=Count('id')).order_by('-count')
    
    # Recent Activities (using StockAdjustment as audit trail)
    recent_activity = StockAdjustment.objects.all().order_by('-timestamp')[:5]

    context = {
        'dashboard_title': 'Warehouse Manager Dashboard',
        'current_stock_levels': {
            'total_items': total_items,
            'in_stock': in_stock_count,
            'low_stock': low_stock_count,
            'out_of_stock': out_of_stock_count,
            'categories': stock_by_category.count()
        },
        'stock_by_category': stock_by_category, # Pass to template
        'recent_activity': recent_activity,
        'low_stock_items': InventoryItem.objects.filter(quantity__lte=F('reorder_point'))[:5]
    }
    return render(request, 'warehouse_manager/dashboard.html', context)

# ==========================================
# 2. INVENTORY LIST
# ==========================================
@login_required
def warehouse_inventory_view(request):
    if request.user.role != 'warehouse_manager' and not request.user.is_superuser:
        return redirect('home')
    
    # Start with all items
    items_query = InventoryItem.objects.all().order_by('name')
    
    # Search Filter
    search_query = request.GET.get('search', '')
    if search_query:
        items_query = items_query.filter(name__icontains=search_query)
        
    # Category Filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        items_query = items_query.filter(category=category_filter)

    # Pagination (10 items per page)
    paginator = Paginator(items_query, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Stats for the top of the page
    stats = {
        'total_items': InventoryItem.objects.count(),
        'in_stock': InventoryItem.objects.filter(quantity__gt=F('reorder_point')).count(),
        'low_stock': InventoryItem.objects.filter(quantity__lte=F('reorder_point'), quantity__gt=0).count(),
        'out_of_stock': InventoryItem.objects.filter(quantity__lte=0).count()
    }

    context = {
        'inventory_items': page_obj, # The list for the table
        'page_obj': page_obj,        # For pagination controls
        'inventory_stats': stats,
    }
    return render(request, 'warehouse_manager/inventory.html', context)

# ==========================================
# 3. ADD ITEM
# ==========================================
@login_required
def warehouse_add_item_view(request):
    if request.user.role != 'warehouse_manager' and not request.user.is_superuser:
        return redirect('home')
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            # Automatically log the initial stock as an adjustment
            StockAdjustment.objects.create(
                item=item,
                user=request.user,
                adjustment_type='set',
                quantity_change=item.quantity,
                reason='Initial Setup',
                notes='Item created via Add Item form'
            )
            messages.success(request, f'Item "{item.name}" added successfully!')
            return redirect('warehouse_inventory')
        else:
            messages.error(request, 'Error adding item. Please check the form.')
    else:
        form = InventoryItemForm()
    
    return render(request, 'warehouse_manager/add_item.html', {'form': form})

# ==========================================
# 4. UPDATE STOCK
# ==========================================
@login_required
def warehouse_update_stock_view(request, item_id):
    if request.user.role != 'warehouse_manager' and not request.user.is_superuser:
        return redirect('home')
    
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            adj_type = form.cleaned_data['adjustment_type']
            qty_input = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']
            notes = form.cleaned_data['notes']
            reference = form.cleaned_data['reference']
            
            old_qty = item.quantity
            change_amount = 0
            
            # Logic for updating quantity
            if adj_type == 'receive':
                item.quantity += qty_input
                change_amount = qty_input
            elif adj_type == 'damage':
                item.quantity -= qty_input
                change_amount = -qty_input
            elif adj_type == 'adjust':
                # Assuming positive input means add, if they want subtract they might use 'damage'
                # Or you can allow negative inputs in the form.
                item.quantity += qty_input
                change_amount = qty_input
            elif adj_type == 'set':
                change_amount = qty_input - old_qty
                item.quantity = qty_input

            item.save()
            
            # Create Audit Log
            StockAdjustment.objects.create(
                item=item,
                user=request.user,
                adjustment_type=adj_type,
                quantity_change=change_amount,
                reason=reason,
                reference=reference,
                notes=notes
            )
            
            messages.success(request, f'Stock updated. New quantity: {item.quantity}')
            return redirect('warehouse_inventory')
    else:
        form = StockUpdateForm()
    
    # Get history for this item
    recent_adjustments = StockAdjustment.objects.filter(item=item).order_by('-timestamp')[:10]
    
    context = {
        'item': item,
        'form': form,
        'recent_adjustments': recent_adjustments
    }
    return render(request, 'warehouse_manager/update_stock.html', context)

# ==========================================
# 5. RECEIVING (Placeholder/Basic)
# ==========================================
@login_required
def warehouse_receiving_view(request):
    # This View would likely list Purchase Orders with status 'sent' 
    # waiting to be received. For now, we render the template.
    return render(request, 'warehouse_manager/receiving.html')

@login_required
def warehouse_new_receiving_view(request):
    return render(request, 'warehouse_manager/new_receiving.html')