from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import login_user, logout_user, register_user, user_profile
# from .auth_views import login_user, logout_user, get_user_profile
from .views import (
    CategoryViewSet,
    ProductViewSet,
    SalesRecordViewSet,
    register_user,
    user_profile  # ✅ Now `user_profile` exists
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'sales', SalesRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("user-profile/", user_profile, name="user-profile"),  # ✅ Ensure it's correctly imported
    path("register/", register_user, name="register_user"),
]


