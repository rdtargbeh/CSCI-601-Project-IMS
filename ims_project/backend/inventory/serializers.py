from rest_framework import serializers
from .models import (
    Category, Product, SalesRecord, Supplier, 
    Inventory, Warehouse, Transaction , User, Report
    ) 



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        # fields = ['id', 'username', 'full_name', 'phone', 'address', 'role']


#  Categories ++++++++++++++++++++++++++++++++++++++
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

#  Products ++++++++++++++++++++++++++++++++++++++
class ProductSerializer(serializers.ModelSerializer):
    low_stock_warning = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_low_stock_warning(self, obj):
        """Return a warning message if stock is below threshold."""
        if obj.stock < obj.low_stock_threshold:
            return f"⚠️ Warning: {obj.product_name} stock is below the threshold ({obj.low_stock_threshold}). Please restock!"
        return None  # No warning if stock is okay

#  Inventories ++++++++++++++++++++++++++++++++++++++
class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.product_name")
    warehouse_name = serializers.ReadOnlyField(source="warehouse.name")
    last_transaction_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id',
            'product_name',
            'warehouse_name',
            'quantity',
            'incoming_stock',
            'outgoing_stock',
            'batch_number',
            'last_stock_check',
            'last_updated',
            'low_stock_threshold',
            'last_transaction_type',
        ]

    def get_last_transaction_type(self, obj):
        # Attempt to fetch the latest transaction for the product
        last_txn = obj.product.transaction_set.order_by('-transaction_date').first()
        return last_txn.transaction_type if last_txn else None


#  Warehouse  ++++++++++++++++++++++++++++++++++++++
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"

#  Suppliers ++++++++++++++++++++++++++++++++++++++
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

    def validate(self, data):
        errors = []
        if not data.get("supplier_name"):
            errors.append("Supplier name is required")
        if not data.get("phone_number"):
            errors.append("Phone number is required")
        # Add checks for other required fields

        if errors:
            raise serializers.ValidationError(errors)

        return data


class SalesRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRecord
        # fields = ['id', 'name', 'location'] 
        fields = "__all__"

#  Transactions ++++++++++++++++++++++++++++++++++++++
class TransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.product_name")
    from_warehouse = WarehouseSerializer(read_only=True)
    to_warehouse = WarehouseSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['transaction_by']

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            validated_data["transaction_by"] = full_name
        return super().create(validated_data)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'report_type', 'format', 'data_range_start', 'data_range_end', 'generated_date']
        read_only_fields = ['id', 'generated_date']