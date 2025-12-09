from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import InventoryItem, RequisitionForm, RequisitionItem, InternalDelivery

@login_required
def staff_dashboard_view(request):
    # Stats Calculation
    available_beverages = InventoryItem.objects.count()
    categories = InventoryItem.objects.values('category').distinct().count()
    
    # Logic: Sales Dept sees ALL history; Others see OWN history
    if request.user.department == 'Sales Department':
        my_requisitions_count = RequisitionForm.objects.count()
        pending_approvals = RequisitionForm.objects.filter(
            status__in=['pending_dept_head', 'pending_vp']
        ).count()
        recent_requisitions = RequisitionForm.objects.all().order_by('-date_created')[:5]
    else:
        my_requisitions_count = RequisitionForm.objects.filter(requester=request.user).count()
        pending_approvals = RequisitionForm.objects.filter(
            requester=request.user, 
            status__in=['pending_dept_head', 'pending_vp']
        ).count()
        recent_requisitions = RequisitionForm.objects.filter(requester=request.user).order_by('-date_created')[:5]
    
    inventory_alerts = InventoryItem.objects.filter(quantity__lte=20)[:5]
    popular_beverages = InventoryItem.objects.all()[:4]

    context = {
        'available_beverages': available_beverages,
        'categories': categories,
        'my_requisitions': my_requisitions_count,
        'pending_approvals': pending_approvals,
        'recent_requisitions': recent_requisitions,
        'inventory_alerts': inventory_alerts,
        'popular_beverages': popular_beverages,
    }
    return render(request, 'staff/dashboard.html', context)

@login_required
def staff_inventory_view(request):
    # RESTRICTION: Sales Department cannot browse inventory
    if request.user.department == 'Sales Department':
        messages.error(request, "Access Denied: Sales Department cannot browse inventory.")
        return redirect('staff_dashboard')

    items = InventoryItem.objects.all().order_by('name')
    
    search = request.GET.get('search')
    category = request.GET.get('category')
    
    if search:
        items = items.filter(name__icontains=search)
    if category:
        items = items.filter(category=category)
        
    context = {
        'inventory_items': items,
    }
    return render(request, 'staff/inventory.html', context)

@login_required
def staff_requisition_view(request):
    # RESTRICTION: Only Requesting Party Department can submit new requests
    if request.user.department != 'Requesting Party Department':
        messages.error(request, "Access Denied: Only the Requesting Party Department can submit new requests.")
        return redirect('staff_dashboard')

    if request.method == 'POST':
        purpose = request.POST.get('purpose')
        notes = request.POST.get('notes')
        
        item_ids = request.POST.getlist('item_ids')
        quantities = request.POST.getlist('item_quantities')
        
        if not item_ids:
            messages.error(request, "Please add at least one item.")
            return redirect('staff_requisition')

        last_rf = RequisitionForm.objects.last()
        next_id = 1 if not last_rf else last_rf.id + 1
        rf_number = f"RF-{timezone.now().year}-{next_id:04d}"
        
        rf = RequisitionForm.objects.create(
            requester=request.user,
            rf_number=rf_number,
            department=request.user.department or "General",
            purpose=purpose,
            notes=notes,
            status='pending_dept_head',
            route_destination='purchasing' 
        )
        
        for i in range(len(item_ids)):
            item = get_object_or_404(InventoryItem, id=item_ids[i])
            stock_available = item.quantity >= int(quantities[i])
            
            RequisitionItem.objects.create(
                requisition=rf,
                item=item,
                quantity_requested=int(quantities[i]),
                stock_available_at_check=stock_available 
            )
        
        rf.save()
        messages.success(request, f"Requisition {rf_number} submitted to Purchasing for review.")
        return redirect('staff_my_requisitions')

    items = InventoryItem.objects.all().order_by('name')
    return render(request, 'staff/submit_requisition.html', {'inventory_items': items})

@login_required
def staff_my_requisitions_view(request):
    # RESTRICTION: Requesting Party cannot view History
    if request.user.department == 'Requesting Party Department':
         messages.error(request, "Access Denied: History is view-only for Sales Department.")
         return redirect('staff_dashboard')

    if request.user.department == 'Sales Department':
        requisitions = RequisitionForm.objects.all().order_by('-date_created')
    else:
        requisitions = RequisitionForm.objects.filter(requester=request.user).order_by('-date_created')
    
    stats = {
        'approved': requisitions.filter(status='approved').count(),
        'pending': requisitions.filter(status__in=['pending_dept_head', 'pending_vp']).count(),
        'closed': requisitions.filter(status='closed').count(),
        'rejected': requisitions.filter(status='rejected').count(),
    }
    
    context = {
        'requisitions': requisitions,
        'stats': stats
    }
    return render(request, 'staff/my_requisitions.html', context)

@login_required
def staff_requisition_detail_view(request, req_id):
    if request.user.department == 'Sales Department':
        req = get_object_or_404(RequisitionForm, id=req_id)
    else:
        req = get_object_or_404(RequisitionForm, id=req_id, requester=request.user)
    
    context = {
        'req': req
    }
    return render(request, 'staff/requisition_detail.html', context)

# NEW: Action to Mark Items as Delivered (Return as Sales)
@login_required
def staff_confirm_delivery_view(request, req_id):
    req = get_object_or_404(RequisitionForm, id=req_id)
    
    # Logic: Mark as Closed (Delivered)
    # This transitions the request to a "Completed Sale" state in the system
    
    # 1. Update Requisition Status
    req.status = 'closed'
    req.save()
    
    # 2. Log Internal Delivery (Acknowledgment)
    InternalDelivery.objects.update_or_create(
        requisition=req,
        defaults={
            'date_delivered': timezone.now(),
            'acknowledgement_receipt_signed': True,
            'received_by_staff_name': request.user.get_full_name()
        }
    )
    
    messages.success(request, f"Requisition {req.rf_number} marked as DELIVERED. Recorded as Sales.")
    return redirect('staff_requisition_detail', req_id=req.id)