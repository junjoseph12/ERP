from django.urls import path
from . import v_views as views
from . import v_admin_views as admin_views
from . import v_purchasing_views as purchasing_views
from . import v_staff_views as staff_views
from . import v_warehouse_views as warehouse_views

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # System Admin URLs
    path('system-admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('system-admin/users/', admin_views.admin_user_management_view, name='admin_users'),
    path('admin/user/<int:user_id>/edit/', admin_views.admin_edit_user_view, name='admin_edit_user'),
    path('system-admin/settings/', admin_views.admin_system_settings_view, name='admin_settings'),
    
    # User Management URLs
    path('system-admin/users/approve/<int:user_id>/', admin_views.admin_approve_user_view, name='admin_approve_user'),
    path('system-admin/users/reject/<int:user_id>/', admin_views.admin_reject_user_view, name='admin_reject_user'),
    path('system-admin/users/suspend/<int:user_id>/', admin_views.admin_suspend_user_view, name='admin_suspend_user'),
    path('system-admin/users/reactivate/<int:user_id>/', admin_views.admin_reactivate_user_view, name='admin_reactivate_user'),
    path('system-admin/users/detail/<int:user_id>/', admin_views.admin_user_detail_view, name='admin_user_detail'),
    
    # Warehouse Manager URLs
    path('warehouse/dashboard/', warehouse_views.warehouse_dashboard_view, name='warehouse_dashboard'),
    path('warehouse/inventory/', warehouse_views.warehouse_inventory_view, name='warehouse_inventory'),
    path('warehouse/receiving/', warehouse_views.warehouse_receiving_view, name='warehouse_receiving'),
    path('warehouse/inventory/add/', warehouse_views.warehouse_add_item_view, name='warehouse_add_item'),
    path('warehouse/inventory/update/<int:item_id>/', warehouse_views.warehouse_update_stock_view, name='warehouse_update_stock'),
    path('warehouse/receiving/new/', warehouse_views.warehouse_new_receiving_view, name='warehouse_new_receiving'),
    path('warehouse/receiving/process/<int:po_id>/', warehouse_views.warehouse_process_receiving_view, name='warehouse_process_receiving'),
    
    # Purchasing Officer URLs
    path('purchasing/dashboard/', purchasing_views.purchasing_dashboard_view, name='purchasing_dashboard'),
    path('purchasing/requisitions/', purchasing_views.purchasing_requisitions_view, name='purchasing_requisitions'),
    path('purchasing/orders/', purchasing_views.purchasing_orders_view, name='purchasing_orders'),
    path('purchasing/suppliers/', purchasing_views.purchasing_suppliers_view, name='purchasing_suppliers'),
    path('purchasing/suppliers/add/', purchasing_views.purchasing_add_supplier_view, name='purchasing_add_supplier'),
    path('purchasing/requisitions/', purchasing_views.purchasing_requisitions_view, name='purchasing_requisitions'),
    path('purchasing/requisitions/<int:req_id>/', purchasing_views.purchasing_requisition_detail_view, name='purchasing_requisition_detail'), # NEW
    path('purchasing/requisitions/reject/<int:req_id>/', purchasing_views.purchasing_reject_requisition_view, name='purchasing_reject_requisition'), # NEW
    path('purchasing/orders/create/', purchasing_views.purchasing_create_po_view, name='purchasing_create_po'),
    path('purchasing/requisitions/forward/<int:req_id>/', purchasing_views.purchasing_approve_to_warehouse_view, name='purchasing_approve_to_warehouse'),
    path('purchasing/orders/status/<int:po_id>/<str:new_status>/', purchasing_views.purchasing_update_po_status_view, name='purchasing_update_po_status'),
    
    # Staff URLs
    path('staff/dashboard/', staff_views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/inventory/', staff_views.staff_inventory_view, name='staff_inventory'),
    path('staff/requisition/', staff_views.staff_requisition_view, name='staff_requisition'),
    path('staff/my-requisitions/', staff_views.staff_my_requisitions_view, name='staff_my_requisitions'),
    path('staff/my-requisitions/<int:req_id>/', staff_views.staff_requisition_detail_view, name='staff_requisition_detail'),
    path('staff/requisition/deliver/<int:req_id>/', staff_views.staff_confirm_delivery_view, name='staff_confirm_delivery'),
]