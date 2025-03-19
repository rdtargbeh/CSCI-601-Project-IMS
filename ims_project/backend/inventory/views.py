from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import json
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated  # ✅ Import DRF authentication
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Category, Product, SalesRecord, Supplier  
from .serializers import CategorySerializer, ProductSerializer, SalesRecordSerializer, SupplierSerializer


User = get_user_model()

#  USER PROFILE VIEW  +++++++++++++++++++++++++++++++++++++++
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Retrieve the logged-in user's profile details."""
    user = request.user

    if request.method == "GET":
        return JsonResponse({
            "username": user.username,
            "fullName": user.get_full_name(),
            "email": user.email,
            "phone": user.phone if hasattr(user, "phone") else None,
            "address": user.address if hasattr(user, "address") else None,
            "profilePic": user.profile_picture.url if hasattr(user, "profile_picture") and user.profile_picture else None,
        })

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            user.full_name = data.get("fullName", user.full_name)
            user.phone = data.get("phone", user.phone)
            user.address = data.get("address", user.address)
            user.save()
            return JsonResponse({"message": "Profile updated successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

# REGISTER USER VIEW ++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=data["role"]
            )
            user.phone = data.get("phone", "")  # ✅ Store phone number
            user.address = data.get("address", "")  # ✅ Store address
            user.save()
            return JsonResponse({"message": "User registered successfully!"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)


#  LOGIN USER VIEW  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def login_user(request):
    """Authenticate user and return a token."""
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({
                "message": "Login successful",
                "token": token.key,
                "role": user.role,  # ✅ Include user role in response
            })
        return JsonResponse({"error": "Invalid credentials"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and delete the token."""
    request.auth.delete()
    return JsonResponse({"message": "Logged out successfully!"})



#  CATEGORY VIEW  +++++++++++++++++++++++++++++++++++++++++++
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("-date_created")
    serializer_class = CategorySerializer

    @action(detail=True, methods=["delete"])
    def delete_category(self, request, pk=None):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        return Response({"message": "Category deleted successfully"}, status=204)



#  PRODUCT VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-date_updated")
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser)  # ✅ Handle file uploads
    permission_classes = [IsAuthenticated]  # ✅ Restrict access to logged-in users

    def destroy(self, request, *args, **kwargs):
        """Allow only admins to delete products"""
        if not request.user.is_staff:
            return Response({"error": "You are not authorized to delete products"}, status=403)
        return super().destroy(request, *args, **kwargs)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer



# ✅ Move the ViewSet inside a function to avoid circular import issues
def get_viewsets():
 
    class ProductViewSet(viewsets.ModelViewSet):
        queryset = Product.objects.all()
        serializer_class = ProductSerializer

    class SalesRecordViewSet(viewsets.ModelViewSet):
        queryset = SalesRecord.objects.all()
        serializer_class = SalesRecordSerializer

    return CategoryViewSet, ProductViewSet, SalesRecordViewSet

# ✅ Use this in `urls.py`
CategoryViewSet, ProductViewSet, SalesRecordViewSet = get_viewsets()

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    """API endpoint for managing products."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


    