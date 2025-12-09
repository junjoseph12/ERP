from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from django.http import HttpResponse  
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import PurchaseOrder, Supplier, RequisitionForm, PurchaseOrderItem, InventoryItem, StockAdjustment
from .forms import SupplierForm, PurchaseOrderForm

# ==========================================
# 1. DASHBOARD
# ==========================================
@login_required
def purchasing_dashboard_view(request):
    if request.user.role != 'purchasing_officer' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Purchasing privileges required.')
        return redirect('home')
    
    context = {
        'pending_requisitions': RequisitionForm.objects.filter(route_destination='purchasing').exclude(status='closed').count(),
        'active_pos': PurchaseOrder.objects.filter(status__in=['ordered', 'in_transit']).count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
        'awaiting_approval': 0, # Concept removed for streamlined flow
        
        'recent_requisitions': RequisitionForm.objects.filter(route_destination='purchasing').order_by('-date_created')[:5],
        'recent_pos': PurchaseOrder.objects.all().order_by('-date_created')[:5],
        'active_suppliers': Supplier.objects.filter(is_active=True)[:5]
    }
    return render(request, 'purchasing_officer/dashboard.html', context)

# ==========================================
# 2. REQUISITIONS MANAGEMENT
# ==========================================
@login_required
def purchasing_requisitions_view(request):
    requisitions = RequisitionForm.objects.filter(
        route_destination='purchasing'
    ).exclude(
        status__in=['closed', 'rejected', 'approved']
    ).order_by('-date_created')
    
    context = {
        'requisitions': requisitions
    }
    return render(request, 'purchasing_officer/requisitions.html', context)

@login_required
def purchasing_requisition_detail_view(request, req_id):
    req = get_object_or_404(RequisitionForm, id=req_id)
    
    total_cost = 0
    for item in req.items.all():
        cost = item.item.cost_price if item.item.cost_price else 0
        total_cost += cost * item.quantity_requested

    context = {
        'req': req,
        'total_cost': total_cost
    }
    return render(request, 'purchasing_officer/requisition_detail.html', context)

@login_required
def purchasing_reject_requisition_view(request, req_id):
    req = get_object_or_404(RequisitionForm, id=req_id)
    req.status = 'rejected'
    req.save()
    messages.success(request, f'Requisition {req.rf_number} has been rejected.')
    return redirect('purchasing_requisitions')

@login_required
def purchasing_approve_to_warehouse_view(request, req_id):
    req = get_object_or_404(RequisitionForm, id=req_id)
    
    for req_item in req.items.all():
        inventory_item = req_item.item
        inventory_item.quantity -= req_item.quantity_requested
        inventory_item.save()
        
        StockAdjustment.objects.create(
            item=inventory_item,
            user=request.user,
            adjustment_type='issue', 
            quantity_change=-req_item.quantity_requested, 
            reason=f'Requisition {req.rf_number} Approved',
            reference=req.rf_number,
            notes=f'Stock confirmed physically by Purchasing. Deducted for Department: {req.department}'
        )
    
    req.status = 'approved'
    req.route_destination = 'warehouse' 
    req.save()
    
    messages.success(request, f'Requisition {req.rf_number} approved. Stock deducted and ticket forwarded to Warehouse.')
    return redirect('purchasing_requisitions')

# ==========================================
# 3. PURCHASE ORDERS
# ==========================================
@login_required
def purchasing_orders_view(request):
    orders = PurchaseOrder.objects.all().order_by('-date_created')
    
    # --- ADDED: Check for auto-download flag ---
    auto_download_po_id = request.session.pop('pdf_download_po_id', None)
    
    context = {
        'orders': orders,
        'auto_download_po_id': auto_download_po_id # Pass to template
    }
    return render(request, 'purchasing_officer/orders.html', context)

@login_required
def purchasing_create_po_view(request):
    initial_data = {}
    linked_req = None
    rf_id = request.GET.get('rf_id')
    
    if rf_id:
        linked_req = get_object_or_404(RequisitionForm, id=rf_id)
        initial_data = {'requisition': linked_req}

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.po_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1:03d}"
            
            po.status = 'ordered' 
            po.save()
            
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
                
                if po.requisition:
                    po.requisition.status = 'in_process'
                    po.requisition.save()

                messages.success(request, f'Purchase Order {po.po_number} created successfully.')
                
                # --- ADDED: Set session flag for auto-download ---
                request.session['pdf_download_po_id'] = po.id
                return redirect('purchasing_orders')
            else:
                messages.error(request, 'Please add items to the PO.')
    else:
        form = PurchaseOrderForm(initial=initial_data)

    inventory_items = InventoryItem.objects.filter(quantity__gte=0) 
    
    return render(request, 'purchasing_officer/create_po.html', {
        'form': form,
        'inventory_items': inventory_items,
        'linked_req': linked_req 
    })

@login_required
def purchasing_download_po_pdf_view(request, po_id):
    if request.user.role not in ['purchasing_officer', 'admin'] and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Calculate Grand Total
    grand_total = sum(item.total_price for item in po.items.all())

    context = {
        'po': po,
        'items': po.items.all(),
        'grand_total': grand_total,
        'generated_at': timezone.now()
    }
    
    template_path = 'purchasing_officer/po_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{po.po_number}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
# ==========================================
# 4. UPDATE PO STATUS (NEW)
# ==========================================
@login_required
def purchasing_update_po_status_view(request, po_id, new_status):
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if new_status == 'in_transit':
        po.status = 'in_transit'
        po.save()
        messages.success(request, f"PO {po.po_number} marked as IN TRANSIT. Warehouse notified.")
    elif new_status == 'cancelled':
        po.status = 'cancelled'
        po.save()
        messages.warning(request, f"PO {po.po_number} cancelled.")
        
    return redirect('purchasing_orders')

# ==========================================
# 5. SUPPLIERS
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

@login_required
def purchasing_edit_supplier_view(request, supplier_id):
    if request.user.role not in ['purchasing_officer', 'admin'] and not request.user.is_superuser:
        messages.error(request, "Access denied. You do not have permission to edit suppliers.")
        return redirect('home')
        
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
            return redirect('purchasing_suppliers')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'purchasing_officer/edit_supplier.html', {'form': form, 'supplier': supplier})