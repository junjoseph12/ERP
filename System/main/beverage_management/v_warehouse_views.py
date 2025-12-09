from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Sum, Count
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template # Added
from xhtml2pdf import pisa # Added (Make sure to pip install xhtml2pdf)

from .models import InventoryItem, StockAdjustment, ReceivingReport, InternalDelivery, PurchaseOrder
from .forms import InventoryItemForm, StockUpdateForm, ReceivingForm

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
    
    # RESTRICTION: Explicitly block Sales Department
    if request.user.department == 'Sales Department':
        messages.error(request, "Access Denied: Sales Department cannot add inventory items.")
        return redirect('staff_dashboard')
    
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
# 5. RECEIVING MODULE
# ==========================================

@login_required
def warehouse_receiving_view(request):
    if request.user.role != 'warehouse_manager':
        return redirect('home')
    
    incoming_pos = PurchaseOrder.objects.filter(status='in_transit').order_by('date_created')
    received_history = ReceivingReport.objects.all().order_by('-date_received')[:10]
    
    # --- ADDED: Check if there is a pending PDF to download ---
    auto_download_rm_id = request.session.pop('pdf_download_rm_id', None)
    
    context = {
        'incoming_pos': incoming_pos,
        'received_history': received_history,
        'auto_download_rm_id': auto_download_rm_id # Pass this to the template
    }
    return render(request, 'warehouse_manager/receiving.html', context)

@login_required
def warehouse_process_receiving_view(request, po_id):
    # 1. Permission Check
    if request.user.role != 'warehouse_manager':
        return redirect('home')
        
    # 2. Get the Purchase Order
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # 3. Handle Form Submission (POST)
    if request.method == 'POST':
        form = ReceivingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    report = form.save(commit=False)
                    report.purchase_order = po
                    report.received_by = request.user
                    count = ReceivingReport.objects.count() + 1
                    report.rm_number = f"RM-{count:04d}"
                    
                    if report.quality_check_passed:
                        report.status = 'accepted'
                        
                        # Update Stock
                        for po_item in po.items.all():
                            inventory_item = po_item.item
                            inventory_item.quantity += po_item.quantity
                            inventory_item.save()
                            
                            StockAdjustment.objects.create(
                                item=inventory_item,
                                user=request.user,
                                adjustment_type='receive',
                                quantity_change=po_item.quantity,
                                reason='Purchase Order Received',
                                reference=f"{po.po_number} / {report.rm_number}",
                                notes=f"Received via DR: {report.delivery_receipt_no}"
                            )
                        
                        po.status = 'completed'
                        po.save()
                        messages.success(request, f"Receiving Memo {report.rm_number} generated. Stock updated.")
                    else:
                        report.status = 'rejected'
                        messages.warning(request, "Delivery rejected due to quality check failure.")
                    
                    report.save()
                    
                    # --- SESSION FLAG FOR PDF DOWNLOAD ---
                    request.session['pdf_download_rm_id'] = report.id
                    return redirect('warehouse_receiving')
                    
            except Exception as e:
                messages.error(request, f"Error processing receiving: {str(e)}")
    
    # 4. Handle Page Load (GET) - THIS PART WAS LIKELY MISSING
    else:
        form = ReceivingForm()
        
    # 5. Render the Template - THIS PART WAS LIKELY MISSING
    context = {
        'po': po,
        'form': form,
        'po_items': po.items.all()
    }
    return render(request, 'warehouse_manager/process_receiving.html', context)

@login_required
def warehouse_new_receiving_view(request):
    # This might be deprecated if you are using the specific process_receiving flow
    # But kept to avoid errors if linked elsewhere
    return render(request, 'warehouse_manager/new_receiving.html')

@login_required
def warehouse_download_rm_pdf_view(request, rm_id):
    if request.user.role not in ['warehouse_manager', 'admin'] and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    rm = get_object_or_404(ReceivingReport, id=rm_id)
    
    # Context data for the PDF
    context = {
        'rm': rm,
        'po': rm.purchase_order,
        'items': rm.purchase_order.items.all(),
        'generated_at': timezone.now()
    }
    
    # Render template
    template_path = 'warehouse_manager/rm_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    # 'attachment' forces download. Remove 'attachment;' to view in browser.
    response['Content-Disposition'] = f'attachment; filename="{rm.rm_number}_receipt.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def warehouse_edit_item_details_view(request, item_id):
    if request.user.role not in ['warehouse_manager', 'admin'] and not request.user.is_superuser:
        messages.error(request, "Access denied. You do not have permission to edit items.")
        return redirect('home')
    
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        # We process the form manually or exclude quantity to prevent stock manipulation here
        item.name = request.POST.get('name')
        item.brand = request.POST.get('brand')
        item.category = request.POST.get('category')
        item.sku = request.POST.get('sku')
        item.location = request.POST.get('location')
        item.description = request.POST.get('description')
        item.unit = request.POST.get('unit')
        item.reorder_point = request.POST.get('reorder_point')
        
        # Save changes
        item.save()
        messages.success(request, f'Details for "{item.name}" updated. Stock was not changed.')
        return redirect('warehouse_inventory')
        
    return render(request, 'warehouse_manager/edit_item_details.html', {'item': item})