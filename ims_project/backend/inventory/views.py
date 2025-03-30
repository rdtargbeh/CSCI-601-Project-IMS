from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import json
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated  # ✅ Import DRF authentication
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from .models import Category, Product, SalesRecord, Supplier, Inventory, Warehouse , Transaction, User, Report 
from .serializers import (
    CategorySerializer, ProductSerializer, SalesRecordSerializer, SupplierSerializer,
    InventorySerializer, WarehouseSerializer, TransactionSerializer, ReportSerializer 
    )


User = get_user_model()

#  USER PROFILE VIEW  +++++++++++++++++++++++++++++++++++++++
@api_view(["GET", "PUT"])  # Allow both GET and PUT methods
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Retrieve or update the logged-in user's profile details."""
    user = request.user  # Get the logged-in user

    if request.method == "GET":
        # Return the user's profile details in response
        return JsonResponse({
            "username": user.username,
            "fullName": user.full_name,
            "email": user.email,
            "phone": user.phone if hasattr(user, "phone") else None,
            "address": user.address if hasattr(user, "address") else None,
            "role": user.role,
            "profilePic": user.profile_picture.url if hasattr(user, "profile_picture") and user.profile_picture else None,
        })

    if request.method == "PUT":
        # Handle profile update logic
        try:
            data = json.loads(request.body)
            user.full_name = data.get("fullName", user.full_name)
            user.phone = data.get("phone", user.phone)
            user.address = data.get("address", user.address)
            user.role = data.get("role", user.role)  # If needed, update the role
            if 'profilePic' in data:
                user.profile_picture = data['profilePic']  # Handle the profile picture if provided

            user.save()
            return JsonResponse({"message": "Profile updated successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


class UserListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    def get(self, request):
        users = User.objects.all()  # Get all users from the database
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


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
@csrf_exempt  # ✅ Temporarily disable CSRF for login
@api_view(["POST"])
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


#  LOGOUT VIEW  +++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and delete the token."""
    request.auth.delete()
    return JsonResponse({"message": "Logged out successfully!"})


#  DASHBOARD VIEW  +++++++++++++++++++++++++++++++++++++++++++
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    # 1. Available inventory: sum of all Product.stock values.
    available_inventory = Product.objects.aggregate(total=Sum('stock'))['total'] or 0

    # 2. Aggregate SalesRecord fields.
    sales_agg = SalesRecord.objects.aggregate(
        total_sale_amount=Sum('total_sale_amount'),
        total_purchase_amount=Sum('total_purchase_amount'),
        total_quantity_purchased=Sum('total_quantity_purchased'),
        total_quantity_sold=Sum('total_quantity_sold')
    )
    total_sale_amount = sales_agg.get('total_sale_amount') or 0
    total_purchase_amount = sales_agg.get('total_purchase_amount') or 0
    total_inventory_purchased = sales_agg.get('total_quantity_purchased') or 0
    total_inventory_sold = sales_agg.get('total_quantity_sold') or 0

    # 3. Calculate profit/loss using per-transaction logic.
    transactions = Transaction.objects.filter(transaction_type__in=["Sale", "Damaged", "Expired"])
    total_profit = 0
    for txn in transactions:
        if txn.transaction_type == "Sale":
            # Profit = (sale unit price - buying price) * quantity sold.
            total_profit += (txn.unit_price - txn.product.buying_price) * txn.quantity
        elif txn.transaction_type in ["Damaged", "Expired"]:
            # Loss due to damage/expiration: cost of items lost.
            total_profit -= txn.product.buying_price * txn.quantity

    profit_display = total_profit if total_profit >= 0 else 0
    loss_display = abs(total_profit) if total_profit < 0 else 0

    # 4. Recent transactions (last 10).
    recent_transactions_qs = Transaction.objects.order_by('-transaction_date')[:10]
    recent_transactions = TransactionSerializer(recent_transactions_qs, many=True).data

    # 5. Recent reports (last 6).
    recent_reports_qs = Report.objects.order_by('-generated_date')[:6]
    recent_reports = [
        {"id": rep.id, "title": rep.title, "generated_date": rep.generated_date}
        for rep in recent_reports_qs
    ]

    data = {
        "available_inventory": available_inventory,
        "total_sale_amount": total_sale_amount,
        "total_purchase_amount": total_purchase_amount,
        "total_inventory_purchased": total_inventory_purchased,
        "total_inventory_sold": total_inventory_sold,
        "profit": round(profit_display, 2),
        "loss": round(loss_display, 2),
        "recent_transactions": recent_transactions,
        "recent_reports": recent_reports,
    }
    
    return Response(data)



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
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        response_data = {
            "message": "Product added successfully!",
            "product": ProductSerializer(product).data,
            "warning": product.low_stock_warning if product.low_stock_warning else None,
        }

        print("API Response (Create):", response_data)  # ✅ Debugging
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        response_data = {
            "message": "Product updated successfully!",
            "product": ProductSerializer(product).data,
            "warning": product.low_stock_warning if product.low_stock_warning else None,
        }

        print("API Response (Update):", response_data)  # ✅ Debugging
        return Response(response_data, status=status.HTTP_200_OK)


#  INVENTORY VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().order_by("-last_updated")
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory = serializer.save()

        response_data = {
            "message": "Inventory added successfully!",
            "inventory": InventorySerializer(inventory).data,
        }

        print("API Response (Create):", response_data)  # ✅ Debugging
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        inventory = serializer.save()

        response_data = {
            "message": "Inventory updated successfully!",
            "inventory": InventorySerializer(inventory).data,
        }

        print("API Response (Update):", response_data)  # ✅ Debugging
        return Response(response_data, status=status.HTTP_200_OK)


#  WAREHOUSE VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by("name")
    serializer_class = WarehouseSerializer

    @action(detail=True, methods=["delete"])
    def delete_warehouse(self, request, pk=None):
        warehouse = get_object_or_404(Warehouse, pk=pk)
        warehouse.delete()
        return Response({"message": "Warehouse deleted successfully"}, status=204)


#  SUPPLIER VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer

    def create(self, request, *args, **kwargs):
        print("🔹 Incoming Data:", request.data)  # Debugging: Print incoming request data
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("❌ Validation Errors:", serializer.errors)  # Debugging: Print errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#  TRANSACTION VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new transaction
        """
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Update an existing transaction
        """
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing transaction
        """
        return super().destroy(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        """
        List all transactions
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific transaction
        """
        return super().retrieve(request, *args, **kwargs)
    # User transaction by
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context



#  REPORT VIEW  ++++++++++++++++++++++++++++++++++++++++++++++++++
class ReportCreateView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user.
        serializer.save(user=self.request.user)




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



    