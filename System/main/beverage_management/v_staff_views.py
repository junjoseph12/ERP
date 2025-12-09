from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import InventoryItem, RequisitionForm, RequisitionItem

@login_required
def staff_dashboard_view(request):
    # Stats Calculation
    available_beverages = InventoryItem.objects.count()
    categories = InventoryItem.objects.values('category').distinct().count()
    
    my_requisitions_count = RequisitionForm.objects.filter(requester=request.user).count()
    pending_approvals = RequisitionForm.objects.filter(
        requester=request.user, 
        status__in=['pending_dept_head', 'pending_vp']
    ).count()
    
    # Recent History
    recent_requisitions = RequisitionForm.objects.filter(requester=request.user).order_by('-date_created')[:5]
    
    # Inventory Alerts (Low Stock)
    inventory_alerts = InventoryItem.objects.filter(quantity__lte=20)[:5] # Just top 5
    
    # Popular items (Mock logic: just take first 4 items)
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
    items = InventoryItem.objects.all().order_by('name')
    
    # Filters
    search = request.GET.get('search')
    category = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    
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
    if request.method == 'POST':
        purpose = request.POST.get('purpose')
        notes = request.POST.get('notes')
        
        item_ids = request.POST.getlist('item_ids')
        quantities = request.POST.getlist('item_quantities')
        
        if not item_ids:
            messages.error(request, "Please add at least one item.")
            return redirect('staff_requisition')

        # Generate RF Number
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
            # CHANGE: Route EVERYTHING to Purchasing first
            route_destination='purchasing' 
        )
        
        for i in range(len(item_ids)):
            item = get_object_or_404(InventoryItem, id=item_ids[i])
            # We still record if stock was available at time of request for reference, 
            # but we ignore it for routing.
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
    requisitions = RequisitionForm.objects.filter(requester=request.user).order_by('-date_created')
    
    context = {
        'requisitions': requisitions,
        'stats': {
            'approved': requisitions.filter(status='approved').count(),
            'pending': requisitions.filter(status__in=['pending_dept_head', 'pending_vp']).count(),
            'closed': requisitions.filter(status='closed').count(),
            'rejected': requisitions.filter(status='rejected').count(),
        }
    }
    return render(request, 'staff/my_requisitions.html', context)

@login_required
def staff_requisition_detail_view(request, req_id):
    # Get the specific requisition, ensure it belongs to the current user
    req = get_object_or_404(RequisitionForm, id=req_id, requester=request.user)
    
    context = {
        'req': req
    }
    return render(request, 'staff/requisition_detail.html', context)