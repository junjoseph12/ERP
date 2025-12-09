from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

# ==========================================
# PHASE 1: USER ACCESS
# ==========================================

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'), 
        ('warehouse_manager', 'Warehouse Manager'), 
        ('purchasing_officer', 'Purchasing Officer'), 
        ('staff', 'Staff'), 
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    
    email = models.EmailField(unique=True) 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_approved(self):
        return self.status == 'approved'

# ==========================================
# PHASE 3: INVENTORY MANAGEMENT
# ==========================================

class InventoryItem(models.Model):
    CATEGORY_CHOICES = (
        ('soft_drinks', 'Soft Drinks'),
        ('energy_drinks', 'Energy Drinks'),
        ('juices', 'Juices'),
        ('water', 'Water'),
        ('alcoholic', 'Alcoholic Beverages'),
        ('coffee_tea', 'Coffee/Tea'),
        ('other', 'Other'),
    )

    # ADDED: Dropdown measurements
    UNIT_CHOICES = (
        ('bottles', 'Bottles'),
        ('cans', 'Cans'),
        ('cases', 'Cases'),
        ('packs', 'Packs (6/12)'),
        ('liters', 'Liters'),
        ('kegs', 'Kegs'),
        ('pallets', 'Pallets'),
    )

    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES) 
    brand = models.CharField(max_length=100) 
    
    quantity = models.IntegerField(default=0) 
    reorder_point = models.IntegerField(default=20) 
    
    # CHANGED: Now uses choices=UNIT_CHOICES
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='bottles')
    
    location = models.CharField(max_length=50, help_text="Aisle-Shelf-Bin")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True) 
    supplier_name = models.CharField(max_length=200, blank=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def stock_status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        elif self.quantity < self.reorder_point:
            return 'low_stock' 
        return 'in_stock'

# ==========================================
# PHASE 4: REQUISITION (RF)
# ==========================================

class RequisitionForm(models.Model):
    STATUS_CHOICES = (
        ('pending_dept_head', 'Pending Dept Head Approval'), 
        ('pending_vp', 'Pending VP Approval'), 
        ('approved', 'Approved (Signed)'), 
        ('rejected', 'Rejected'), 
        ('in_process', 'In Process (Warehouse/Purchasing)'),
        ('closed', 'Closed'), 
    )

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions')
    rf_number = models.CharField(max_length=50, unique=True, help_text="Auto-generated RF ID")
    department = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_dept_head')
    
    # --- ADD THESE TWO LINES ---
    purpose = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    # ---------------------------
    
    # Physical Approval Tracking
    is_signed_by_dept_head = models.BooleanField(default=False)
    date_signed_dept_head = models.DateField(null=True, blank=True)
    
    is_signed_by_vp = models.BooleanField(default=False)
    date_signed_vp = models.DateField(null=True, blank=True)
    
    # Routing Logic
    route_destination = models.CharField(
        max_length=20, 
        choices=(('warehouse', 'Warehouse (Pick List)'), ('purchasing', 'Purchasing (PO)')),
        null=True, blank=True
    ) 

    def __str__(self):
        return f"{self.rf_number} - {self.requester} ({self.get_status_display()})"

class RequisitionItem(models.Model):
    requisition = models.ForeignKey(RequisitionForm, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    stock_available_at_check = models.BooleanField(default=False, help_text="Result of system inventory check")

    def __str__(self):
        return f"{self.item.name} ({self.quantity_requested})"

# ==========================================
# PHASE 5: PURCHASING (PO)
# ==========================================

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):

    STATUS_CHOICES = (
        ('ordered', 'Ordered'),       
        ('in_transit', 'In Transit'), 
        ('completed', 'Completed'),   
        ('cancelled', 'Cancelled'),
    )

    po_number = models.CharField(max_length=50, unique=True)
    requisition = models.ForeignKey(RequisitionForm, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'purchasing_officer'})
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    # UPDATED: Default is now 'ordered'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    
    selection_justification = models.TextField(blank=True)
    
    # VP Approval fields are no longer strictly needed for status logic 
    # but can be kept for physical record audit if desired.
    is_signed_by_vp = models.BooleanField(default=False)
    date_signed_vp = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.po_number} - {self.supplier}"

class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) 

    @property
    def total_price(self):
        return self.quantity * self.unit_price

# ==========================================
# PHASE 6: RECEIVING (RM/DR)
# ==========================================

class ReceivingReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Inspection Pending'), 
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected (Damaged/Expired)'),
    )

    rm_number = models.CharField(max_length=50, unique=True, help_text="Receiving Memo #") 
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE) 
    delivery_receipt_no = models.CharField(max_length=100, help_text="Supplier DR #")
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'warehouse_manager'})
    date_received = models.DateTimeField(auto_now_add=True)
    quality_check_passed = models.BooleanField(default=False) 
    inspection_notes = models.TextField(blank=True, help_text="Notes on damages or expiry")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.rm_number} (DR: {self.delivery_receipt_no})"

# ==========================================
# PHASE 7: INTERNAL DELIVERY (Pick List/AR)
# ==========================================

class InternalDelivery(models.Model):
    requisition = models.OneToOneField(RequisitionForm, on_delete=models.CASCADE) 
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'warehouse_manager'})
    date_delivered = models.DateTimeField(null=True, blank=True)
    acknowledgement_receipt_signed = models.BooleanField(default=False) 
    received_by_staff_name = models.CharField(max_length=100, help_text="Name of staff who signed AR")
    date_signed_ar = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.acknowledgement_receipt_signed and self.requisition.status != 'closed':
            self.requisition.status = 'closed'
            self.requisition.save()
        super().save(*args, **kwargs)

# ==========================================
# PHASE 8: REPORTING & AUDIT LOGS
# ==========================================

class StockAdjustment(models.Model):
    TYPE_CHOICES = (
        ('receive', 'Receiving (Add)'),
        ('adjust', 'Manual Adjustment'),
        ('damage', 'Damage/Wastage'),
        ('issue', 'Internal Issue (Deduct)'),
        ('set', 'Set Exact Quantity'),
    )

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='adjustments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) 
    adjustment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity_change = models.IntegerField() 
    reason = models.CharField(max_length=200)
    reference = models.CharField(max_length=100, blank=True, help_text="PO#, RM#, or RF#") 
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now) 

    def __str__(self):
        return f"{self.item.sku} - {self.adjustment_type} ({self.quantity_change})"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255) 
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"