from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum

from .models import PurchaseOrder, Supplier, RequisitionForm, PurchaseOrderItem, InventoryItem
from .forms import SupplierForm, PurchaseOrderForm

# ==========================================
# 1. DASHBOARD
# ==========================================
@login_required
def purchasing_dashboard_view(request):
    if request.user.role != 'purchasing_officer' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Purchasing privileges required.')
        return redirect('home')
    
    # Real DB Stats
    context = {
        'pending_requisitions': RequisitionForm.objects.filter(route_destination='purchasing').exclude(status='closed').count(),
        'active_pos': PurchaseOrder.objects.filter(status__in=['approved', 'sent']).count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
        'awaiting_approval': PurchaseOrder.objects.filter(status='pending_approval').count(),
        
        # Lists for dashboard tables
        'recent_requisitions': RequisitionForm.objects.filter(route_destination='purchasing').order_by('-date_created')[:5],
        'recent_pos': PurchaseOrder.objects.all().order_by('-date_created')[:5],
        'active_suppliers': Supplier.objects.filter(is_active=True)[:5]
    }
    return render(request, 'purchasing_officer/dashboard.html', context)

# ==========================================
# 2. REQUISITIONS LIST
# ==========================================
@login_required
def purchasing_requisitions_view(request):
    # Show requisitions routed to purchasing (Stock Unavailable)
    requisitions = RequisitionForm.objects.filter(route_destination='purchasing').order_by('-date_created')
    
    context = {
        'requisitions': requisitions
    }
    return render(request, 'purchasing_officer/requisitions.html', context)

# ==========================================
# 3. PURCHASE ORDERS LIST
# ==========================================
@login_required
def purchasing_orders_view(request):
    orders = PurchaseOrder.objects.all().order_by('-date_created')
    return render(request, 'purchasing_officer/orders.html', {'orders': orders})

# ==========================================
# 4. CREATE PO
# ==========================================
@login_required
def purchasing_create_po_view(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        
        # Custom logic to handle dynamic items list from the HTML table
        if form.is_valid():
            # 1. Create the PO Header
            po = form.save(commit=False)
            po.created_by = request.user
            po.po_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1:03d}"
            po.status = 'pending_approval' # Needs VP approval first
            po.save()
            
            # 2. Process Items from the dynamic table
            item_ids = request.POST.getlist('item_ids')
            quantities = request.POST.getlist('quantities')
            prices = request.POST.getlist('prices')
            
            if item_ids:
                for i in range(len(item_ids)):
                    item = get_object_or_404(InventoryItem, id=item_ids[i])
                    PurchaseOrderItem.objects.create(
                        po=po,
                        item=item,
                        quantity=int(quantities[i]),
                        unit_price=float(prices[i])
                    )
                messages.success(request, f'Purchase Order {po.po_number} created successfully!')
                return redirect('purchasing_orders')
            else:
                messages.error(request, 'Please add at least one item to the PO.')
    else:
        form = PurchaseOrderForm()

    # Pass inventory items for the dropdown in the "Add Item" row
    inventory_items = InventoryItem.objects.filter(is_active=True) if hasattr(InventoryItem, 'is_active') else InventoryItem.objects.all()
    
    return render(request, 'purchasing_officer/create_po.html', {
        'form': form,
        'inventory_items': inventory_items
    })

# ==========================================
# 5. SUPPLIER MANAGEMENT
# ==========================================
@login_required
def purchasing_suppliers_view(request):
    suppliers = Supplier.objects.all()
    return render(request, 'purchasing_officer/suppliers.html', {'suppliers': suppliers})

@login_required
def purchasing_add_supplier_view(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully!')
            return redirect('purchasing_suppliers')
    else:
        form = SupplierForm()
    
    return render(request, 'purchasing_officer/add_supplier.html', {'form': form})