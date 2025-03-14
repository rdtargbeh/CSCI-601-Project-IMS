from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
from extensions import db  # Import db from extensions.py


def create_app():
    app = Flask(__name__)

    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ims_user:yourpassword@localhost/inventory_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your_secret_key'

    # Initialize database with app
    db.init_app(app)

    # Import models AFTER db.init_app(app) to avoid circular import
    from models import TransactionTypeEnum, ReportTypeEnum, Transaction, Reports

    # Import routes AFTER app is created
    from routes import setup_routes
    setup_routes(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
