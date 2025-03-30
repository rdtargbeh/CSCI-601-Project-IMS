from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

# Import viewsets (do NOT include ReportCreateView here)
from .views import (
    CategoryViewSet,
    ProductViewSet,
    SalesRecordViewSet,
    register_user,
    user_profile,
    SupplierViewSet,
    InventoryViewSet,
    WarehouseViewSet,
    TransactionViewSet,
    UserListView  # If needed
)

# Import other views separately
from .views import dashboard_stats, ReportCreateView, login_user, logout_user

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"inventory", InventoryViewSet, basename="inventory")
router.register(r'sales', SalesRecordViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("user-profile/", user_profile, name="user-profile"),
    path("register/", register_user, name="register_user"),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('dashboard/', dashboard_stats, name='dashboard-stats'),
    path('reports/', ReportCreateView.as_view(), name='report-create'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import login_user, logout_user, register_user, user_profile, UserListView   
# from django.conf import settings
# from django.conf.urls.static import static
# from .views import dashboard_stats
# from . import views 
# from .views import (
#     CategoryViewSet, ProductViewSet, SalesRecordViewSet,
#     register_user, user_profile, SupplierViewSet,
#     InventoryViewSet, WarehouseViewSet, TransactionViewSet
# )

# from .views import dashboard_stats, ReportCreateView


# router = DefaultRouter()
# router.register(r'categories', CategoryViewSet)
# router.register(r'products', ProductViewSet)
# router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
# router.register(r"inventory", InventoryViewSet, basename="inventory")
# router.register(r'sales', SalesRecordViewSet)
# router.register(r'suppliers', SupplierViewSet)  # This exposes /api/suppliers/
# router.register(r'transactions', TransactionViewSet)



# urlpatterns = [
#     path('', include(router.urls)),
#     path("login/", login_user, name="login"),
#     path("logout/", logout_user, name="logout"),
#     path("user-profile/", user_profile, name="user-profile"),  # ✅ Ensure it's correctly imported
#     path("register/", register_user, name="register_user"),
#     path('api/users/', UserListView.as_view(), name='user-list'), 
#     path('dashboard/', dashboard_stats, name='dashboard-stats')
#     path('reports/', ReportCreateView.as_view(), name='report-create'),
    
# ]


# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # ✅ Serve media files