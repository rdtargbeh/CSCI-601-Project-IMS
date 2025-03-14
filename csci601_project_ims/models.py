
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from extensions import db  # Import db from extensions.py


db = SQLAlchemy()  # Initialize db without app dependency

# 1️⃣ Category Model   ++++++++++++++++++++++++++++++++
class Category(db.Model):
    __tablename__ = 'category'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, default=None)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy=True)  # One-to-Many


# 2️⃣ Product Model  ++++++++++++++++++++++++++++++++++
class Product(db.Model):
    __tablename__ = 'product'

    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    sku = db.Column(db.String(30), unique=True, nullable=False)
    barcode = db.Column(db.String(50), unique=True)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=5)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'), nullable=True)
    expiration_date = db.Column(db.Date)
    image_url = db.Column(db.Text, default=None)
    description = db.Column(db.Text, default=None)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='products', lazy=True)  # Many-to-One


# 3️⃣ Inventory Model  +++++++++++++++++++++++++++++++++++++++++
class Inventory(db.Model):
    __tablename__ = 'inventory'

    inventory_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    warehouse_location = db.Column(db.String(100), default='Main Warehouse')
    batch_number = db.Column(db.String(50), default=None)
    last_stock_check = db.Column(db.Date, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product', backref='inventory', lazy=True)  # Many-to-One


# 4️⃣ Transaction Model  ++++++++++++++++++++++++++++++++++++++++
class Transaction(db.Model):
    __tablename__ = 'transaction'

    transaction_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    transaction_by = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    batch_number = db.Column(db.String(50), default=None)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Completed')

    product = db.relationship('Product', backref='transactions', lazy=True)
    user = db.relationship('User', backref='transactions', lazy=True)


# 5️⃣ User Model  +++++++++++++++++++++++++++++++++++++++++++++++++++
class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, default=None)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), default='Staff')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=None)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# 6️⃣ Supplier Model  +++++++++++++++++++++++++++++++++++++++++++++++++++++
class Supplier(db.Model):
    __tablename__ = 'supplier'

    supplier_id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(50), default=None)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), default=None)
    payment_terms = db.Column(db.String(100), default='Net 30')
    supplier_rating = db.Column(db.Float, default=3.0)


# 7️⃣ Reports Model  ++++++++++++++++++++++++++++++++++++++++++++++++++++++
class Reports(db.Model):
    __tablename__ = 'reports'

    report_id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(20), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    format = db.Column(db.String(10), nullable=False)
    data_range_start = db.Column(db.Date, default=None)
    data_range_end = db.Column(db.Date, default=None)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reports', lazy=True)


# 8️⃣ Relationship Tables (Report_Inventory & Report_Transaction)  +++++++++++++++++++++++++++++
class ReportInventory(db.Model):
    __tablename__ = 'report_inventory'

    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id'), primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.inventory_id'), primary_key=True)

class ReportTransaction(db.Model):
    __tablename__ = 'report_transaction'

    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id'), primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.transaction_id'), primary_key=True)


# Define choices for dropdown lists
class TransactionTypeEnum(Enum):
    SALE = "Sale"
    PURCHASE = "Purchase"
    RETURN = "Return"
    TRANSFER = "Transfer"
    DAMAGED = "Damaged"
    EXPIRED = "Expired"

class ReportTypeEnum(Enum):
    SALES_REPORT = "Sales Report"
    STOCK_REPORT = "Stock Report"
    SUPPLIER_REPORT = "Supplier Report"
    INVENTORY_AUDIT = "Inventory Audit"
    PROFIT_LOSS = "Profit & Loss"