from rest_framework import serializers
from .models import (
    Category, Product, SalesRecord, Supplier, 
    Inventory, Warehouse, Transaction 
    ) 

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

    class Meta:
        model = Inventory
        fields = [
            "id", "product", "product_name", "warehouse", "warehouse_name",
            "quantity", "incoming_stock", "outgoing_stock", "batch_number",
            "last_transaction_type", "last_stock_check", "last_updated",
            "low_stock_threshold"
        ]


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
        fields = "__all__"

#  Transactions ++++++++++++++++++++++++++++++++++++++
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

