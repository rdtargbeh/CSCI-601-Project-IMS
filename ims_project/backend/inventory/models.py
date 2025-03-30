from django.core.exceptions import ValidationError
from django.db import models
from datetime import date
from django.utils.timezone import now
import logging
from django.db.models import Sum
import uuid
from django.contrib.auth.models import AbstractUser, Group, Permission


# Custom User Model
class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=[
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Staff', 'Staff'),
    ], default='Staff')
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    # ✅ Fix related name conflicts
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    def __str__(self):
        return self.username


#  Category Table Model  +++++++++++++++++++++++++++++++++++++++
class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name


#  Warehouse Table Model  +++++++++++++++++++++++++++++++++++++++
class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.location})"


#  Supplier Table Model  +++++++++++++++++++++++++++++++++++++++
class Supplier(models.Model):
    supplier_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    address = models.TextField(null=True, blank=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    payment_terms = models.CharField(max_length=100, default="Net 30")
    supplier_rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name

logger = logging.getLogger(__name__)  # ✅ Logger for low stock warnings


# Product Table +++++++++++++++++++++++++++++++++++++++++
class Product(models.Model):
    product_name = models.CharField(max_length=100)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    sku = models.CharField(max_length=30, unique=True, blank=True, null=True)  # Auto-generated if not provided.
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)  # Aggregated stock from inventories.
    low_stock_threshold = models.PositiveIntegerField(default=3)
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    low_stock_warning = models.TextField(blank=True, null=True) 

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided.
        if not self.sku:
            category_code = self.category.category_name[:3].upper()
            product_code = self.product_name[:3].upper()
            unique_id = str(uuid.uuid4().hex[:4]).upper()
            self.sku = f"{category_code}-{product_code}-{unique_id}"

        # Auto-generate Barcode if not provided.
        if not self.barcode:
            self.barcode = str(uuid.uuid4().hex[:12]).upper()

        # Determine if this is a new instance.
        is_new = self.pk is None

        # If new, save once so a primary key is generated.
        if is_new:
            super().save(*args, **kwargs)

        # Aggregate stock from all related inventories.
        total_stock = self.inventories.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0
        self.stock = total_stock

        # Validations.
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")
        if self.buying_price < 0:
            raise ValidationError("Buying price cannot be negative.")
        if self.selling_price < self.buying_price:
            raise ValidationError("Selling price cannot be lower than the buying price.")
        if self.expiration_date and self.expiration_date < date.today():
            raise ValidationError("Expiration date cannot be in the past.")

        if self.stock < self.low_stock_threshold:
            self.low_stock_warning = f"⚠️ Warning: {self.product_name} stock is low ({self.stock} items remaining). Please restock!"
        else:
            self.low_stock_warning = None

        print(f"Saving Product: {self.product_name}, Warning: {self.low_stock_warning}")

        # For new instances, update the record directly using queryset.update()
        # to avoid calling super().save() twice (which can attempt a duplicate insert).
        if is_new:
            self.__class__.objects.filter(pk=self.pk).update(
                stock=self.stock, low_stock_warning=self.low_stock_warning
            )
        else:
            # For updates, simply call super().save() to update the instance.
            super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name


# Inventory Table  ++++++++++++++++++++++++++++++++++++++++++++++
class Inventory(models.Model):
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventories")
    # product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_stock")
    quantity = models.PositiveIntegerField()
    incoming_stock = models.PositiveIntegerField(default=0)  # ✅ Tracks stock added
    outgoing_stock = models.PositiveIntegerField(default=0)  # ✅ Tracks stock removed
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    last_stock_check = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    low_stock_threshold = models.PositiveIntegerField(default=3)


    def save(self, *args, **kwargs):
        # Prevent negative stock and overselling
        if self.quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")
        if self.outgoing_stock > self.quantity:
            raise ValidationError("Cannot sell more stock than available.")

        # Calculate the new quantity (update based on incoming/outgoing adjustments)
        new_quantity = self.quantity + self.incoming_stock - self.outgoing_stock
        if new_quantity < 0:
            raise ValidationError("Stock update results in negative quantity.")
        self.quantity = new_quantity

        # Update the related product’s aggregated stock across all inventories.
        total_stock = self.product.inventories.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0
        # Instead of self.product.save(), update directly to bypass validations.
        from .models import Product  # Ensure Product is imported
        Product.objects.filter(pk=self.product.pk).update(stock=total_stock)
     
        # Reset the incoming/outgoing trackers after applying the update.
        self.incoming_stock = 0
        self.outgoing_stock = 0

        if self.quantity < self.low_stock_threshold:
            print(f"⚠️ Warning: {self.product.product_name} stock is low ({self.quantity} remaining). Please restock!")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} in stock at {self.warehouse.name}"


# TRANSACTION MODEL   +++++++++++++++++++++++++++++++++++++++++++++
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Sale', 'Sale'),
        ('Purchase', 'Purchase'),
        ('Return', 'Return'),
        ('Transfer', 'Transfer'),
        ('Damaged', 'Damaged'),
        ('Expired', 'Expired'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added field for total price
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_by = models.CharField(max_length=255, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Completed")
    
    # Added fields for transfer transaction type
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name="from_warehouse_transactions")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name="to_warehouse_transactions")


    def save(self, *args, **kwargs):
        # Calculate total price.
        self.total_price = self.unit_price * self.quantity

        # Update inventory and product stock based on transaction type.
        if self.transaction_type == 'Transfer':
            self._handle_transfer()
        else:
            # For Purchase and Return, treat as incoming (stock increases);
            # For Sale, Damaged, or Expired, treat as outgoing (stock decreases).
            is_incoming = self.transaction_type in ['Purchase', 'Return']
            self._update_inventory(incoming=is_incoming, outgoing=(not is_incoming))
        super().save(*args, **kwargs)

        # Update SalesRecord for statistics.
        from .models import SalesRecord
        sale_record, created = SalesRecord.objects.get_or_create(product=self.product)
        sale_record.update_record(self)


    def _update_inventory(self, incoming=False, outgoing=False):
        """
        For non-transfer transactions, update the inventory for a default warehouse.
        (You may adjust the warehouse selection logic based on your requirements.)
        """
        # Use a default warehouse (e.g. the first one in the database).
        default_warehouse = Warehouse.objects.first()
        if not default_warehouse:
            raise ValidationError("No default warehouse found.")

        inventory, created = Inventory.objects.get_or_create(
            product=self.product,
            warehouse=default_warehouse,
            defaults={'quantity': 0, 'incoming_stock': 0, 'outgoing_stock': 0}
        )
        if incoming:
            # inventory.quantity = self.quantity
            inventory.incoming_stock += self.quantity
        else:
            if inventory.quantity < self.quantity:
                raise ValidationError("Not enough stock in the default warehouse for this transaction.")
            # inventory.quantity -= self.quantity
            inventory.outgoing_stock += self.quantity
        inventory.save()

    def _handle_transfer(self):
        """
        For transfers, move stock from the source warehouse to the target warehouse.
        Increase target inventory and decrease source inventory.
        """
        if not (self.from_warehouse and self.to_warehouse):
            raise ValidationError("Both from_warehouse and to_warehouse must be provided for a transfer.")
        if self.from_warehouse == self.to_warehouse:
            raise ValidationError("The from_warehouse and to_warehouse cannot be the same for a transfer.")

        # Get source inventory record; if not found, raise error.
        try:
            source_inventory = Inventory.objects.get(product=self.product, warehouse=self.from_warehouse)
        except Inventory.DoesNotExist:
            raise ValidationError("No inventory record exists for this product in the source warehouse.")

        if source_inventory.quantity < self.quantity:
            raise ValidationError("Not enough stock in the source warehouse for the transfer.")

        # Get or create target inventory record.
        target_inventory, created = Inventory.objects.get_or_create(
            product=self.product,
            warehouse=self.to_warehouse,
            defaults={'quantity': 0, 'incoming_stock': 0, 'outgoing_stock': 0}
        )

        # Adjust source and target inventories.
        source_inventory.outgoing_stock += self.quantity
        source_inventory.save()

        target_inventory.incoming_stock += self.quantity
        target_inventory.save()

    def __str__(self):
        # Including product name in the transaction string.
        return f"{self.transaction_type} - {self.product.product_name} ({self.quantity})"


    

#  SALE RECORD MODEL  ++++++++++++++++++++++++++++++++++++++++
class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    total_quantity_sold = models.PositiveIntegerField(default=0)
    total_sale_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_quantity_purchased = models.PositiveIntegerField(default=0)
    total_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateTimeField(auto_now_add=True)

    def update_record(self, transaction):
        if transaction.transaction_type == "Sale":
            self.total_quantity_sold += transaction.quantity
            self.total_sale_amount += transaction.total_price
        elif transaction.transaction_type == "Purchase":
            self.total_quantity_purchased += transaction.quantity
            self.total_purchase_amount += transaction.total_price
        
        self.save()

    def __str__(self):
        return f"{self.product.product_name} - {self.total_quantity_sold} sold"

#  PAYMENT MODEL +++++++++++++++++++++++++++++++++++++++++++
from django.db import models
from django.core.exceptions import ValidationError

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        # Add more payment methods if required
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Link the payment to a specific transaction
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="payment")
    
    # Payment details
    payment_date = models.DateTimeField(auto_now_add=True)  # Date when the payment was made
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)  # Amount paid for the transaction
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')  # Payment status
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)  # Method of payment (e.g., Credit Card, PayPal)

    # Additional fields to track payment processing (optional)
    payment_gateway_transaction_id  = models.CharField(max_length=100, unique=True)  # Transaction ID from the payment gateway
    payment_reference = models.CharField(max_length=100, blank=True, null=True)  # Optional: Reference number from gateway

    def __str__(self):
        return f"Payment for {self.transaction.product.product_name} - {self.payment_status}"

    def update_payment_status(self, status):
        """
        Updates the payment status and transaction status based on the payment outcome.
        """
        # Update the payment status
        self.payment_status = status
        self.save()

        # Update the transaction status based on payment status
        if status == "Completed":
            self.transaction.status = "Completed"
        elif status == "Failed":
            self.transaction.status = "Failed"
        self.transaction.save()

    def save(self, *args, **kwargs):
        """
        Overridden save method to validate and ensure proper workflow before saving payment.
        """
        if self.amount_paid <= 0:
            raise ValidationError("Amount paid should be greater than zero.")

        if self.transaction.status == "Completed":
            raise ValidationError("Payment has already been completed for this transaction.")
        
        super().save(*args, **kwargs)  # Call the real save method



# Reports Table
class Report(models.Model):
    REPORT_TYPES = [
        ('Sales Report', 'Sales Report'),
        ('Stock Report', 'Stock Report'),
        ('Supplier Report', 'Supplier Report'),
        ('Inventory Audit', 'Inventory Audit'),
        ('Profit & Loss', 'Profit & Loss'),
    ]

    FORMAT_CHOICES = [
        ('CSV', 'CSV'),
        ('PDF', 'PDF'),
        ('Excel', 'Excel'),
    ]


    title = models.CharField(max_length=100, blank=True, null=True, help_text="Optional report title for quick reference")
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    data_range_start = models.DateField(null=True, blank=True)
    data_range_end = models.DateField(null=True, blank=True)
    generated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # If title is provided, use it; otherwise, fall back to report_type and format.
        if self.title:
            return self.title
        return f"{self.report_type} ({self.format})"



# Many-to-Many Relationships for Reports
class ReportInventory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)

    def __str__(self):
        return f"Report {self.report.id} - Inventory {self.inventory.id}"

class ReportTransaction(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)

    def __str__(self):
        return f"Report {self.report.id} - Transaction {self.transaction.id}"



