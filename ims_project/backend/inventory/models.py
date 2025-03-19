from django.db import models
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

# Category Table
class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name

# Supplier Table
class Supplier(models.Model):
    supplier_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    address = models.TextField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, default="Net 30")
    supplier_rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name

# Product Table +++++++++++++++++++++++++++++++++++++++++
class Product(models.Model):
    product_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sku = models.CharField(max_length=30, unique=True, blank=True, null=True)  # ✅ Allow auto-generation
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=5)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            category_code = self.category.category_name[:3].upper()
            product_code = self.product_name[:3].upper()
            unique_id = str(uuid.uuid4().hex[:4]).upper()
            self.sku = f"{category_code}-{product_code}-{unique_id}"

        if not self.barcode:
            self.barcode = str(uuid.uuid4().hex[:12]).upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name

# Inventory Table  ++++++++++++++++++++++++++++++++++++++++++++++
class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    warehouse_location = models.CharField(max_length=100, default="Main Warehouse")
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    last_stock_check = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} in stock"

# Transaction Table   +++++++++++++++++++++++++++++++++++++++++++++
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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Completed")

    def __str__(self):
        return f"{self.transaction_type} - {self.product.product_name} ({self.quantity})"

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

    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    data_range_start = models.DateField(null=True, blank=True)
    data_range_end = models.DateField(null=True, blank=True)
    generated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
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


class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_sold = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity_sold} sold"
