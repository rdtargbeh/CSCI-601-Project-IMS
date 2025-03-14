from flask import render_template, request, redirect, url_for, flash
from models import db, Transaction, TransactionTypeEnum, Reports, ReportTypeEnum
from datetime import datetime

def setup_routes(app):
    @app.route('/new_transaction', methods=['GET', 'POST'])
    def new_transaction():
        if request.method == 'POST':
            product_id = request.form['product_id']
            transaction_type = request.form['transaction_type']
            quantity = int(request.form['quantity'])
            unit_price = float(request.form['unit_price'])
            transaction_by = 1  # Assuming user_id=1 for now

            new_transaction = Transaction(
                product_id=product_id,
                transaction_type=TransactionTypeEnum[transaction_type],
                quantity=quantity,
                unit_price=unit_price,
                total_cost=quantity * unit_price,
                transaction_by=transaction_by,
                transaction_date=datetime.utcnow(),
                status='Completed'
            )
            db.session.add(new_transaction)
            db.session.commit()

            flash("Transaction added successfully!", "success")
            return redirect(url_for('new_transaction'))

        return render_template('new_transaction.html', transaction_types=TransactionTypeEnum)

    @app.route('/generate_report', methods=['GET', 'POST'])
    def generate_report():
        if request.method == 'POST':
            report_type = request.form['report_type']
            generated_by = 1  # Assuming user_id=1 for now
            format = request.form['format']

            new_report = Reports(
                report_type=ReportTypeEnum[report_type],
                generated_by=generated_by,
                format=format,
                generated_date=datetime.utcnow()
            )
            db.session.add(new_report)
            db.session.commit()

            flash("Report generated successfully!", "success")
            return redirect(url_for('generate_report'))

        return render_template('generate_report.html', report_types=ReportTypeEnum)
