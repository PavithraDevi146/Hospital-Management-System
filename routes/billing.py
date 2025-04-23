from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from extensions import supabase_client
from datetime import datetime, timedelta

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

class InvoiceForm(FlaskForm):
    patient_id = SelectField('Patient', validators=[DataRequired()], coerce=str)
    invoice_date = DateField('Invoice Date', validators=[DataRequired()], format='%Y-%m-%d')
    due_date = DateField('Due Date', validators=[DataRequired()], format='%Y-%m-%d')
    amount = DecimalField('Amount ($)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Invoice')

@billing_bp.route('/')
@login_required
def list():
    try:
        # Get filter parameters
        status = request.args.get('status', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Base query
        query = supabase_client.table('invoices').select('*, patients(name)')
        
        # Apply filters
        if status:
            query = query.eq('status', status)
        if start_date:
            query = query.gte('invoice_date', start_date)
        if end_date:
            query = query.lte('invoice_date', end_date)
            
        # Execute query
        response = query.order('invoice_date', desc=True).execute()
        
        invoices = response.data if response.data else []
        return render_template('billing/list.html', invoices=invoices)
    except Exception as e:
        flash(f'Error fetching invoices: {str(e)}', 'danger')
        return render_template('billing/list.html', invoices=[])

@billing_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = InvoiceForm()
    
    # Set default dates
    if request.method == 'GET':
        form.invoice_date.data = datetime.now().date()
        form.due_date.data = (datetime.now() + timedelta(days=30)).date()
    
    # Populate patient dropdown
    try:
        patients_response = supabase_client.table('patients').select('id, name').order('name').execute()
        patients = patients_response.data if patients_response.data else []
        form.patient_id.choices = [(pat['id'], pat['name']) for pat in patients]
    except Exception as e:
        flash(f'Error fetching patients: {str(e)}', 'danger')
        form.patient_id.choices = []
    
    if form.validate_on_submit():
        try:
            # Create invoice in database
            invoice_data = {
                'patient_id': form.patient_id.data,
                'invoice_date': form.invoice_date.data.isoformat(),
                'due_date': form.due_date.data.isoformat(),
                'amount': float(form.amount.data),
                'status': form.status.data,
                'notes': form.notes.data,
                'created_by': current_user.get_id(),
                'created_at': datetime.now().isoformat()
            }
            
            response = supabase_client.table('invoices').insert(invoice_data).execute()
            flash('Invoice created successfully!', 'success')
            return redirect(url_for('billing.list'))
        except Exception as e:
            flash(f'Error creating invoice: {str(e)}', 'danger')
    
    return render_template('billing/create.html', form=form)

@billing_bp.route('/view/<id>')
@login_required
def view(id):
    try:
        # Get invoice details with patient name
        response = supabase_client.table('invoices').select('*, patients(name)').eq('id', id).execute()
        if response.data:
            invoice = response.data[0]
            return render_template('billing/view.html', invoice=invoice)
        else:
            flash('Invoice not found.', 'warning')
            return redirect(url_for('billing.list'))
    except Exception as e:
        flash(f'Error fetching invoice details: {str(e)}', 'danger')
        return redirect(url_for('billing.list'))

@billing_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    form = InvoiceForm()
    
    try:
        # Get invoice details
        response = supabase_client.table('invoices').select('*').eq('id', id).execute()
        if not response.data:
            flash('Invoice not found.', 'warning')
            return redirect(url_for('billing.list'))
        
        invoice = response.data[0]
        
        # Populate patient dropdown
        patients_response = supabase_client.table('patients').select('id, name').order('name').execute()
        patients = patients_response.data if patients_response.data else []
        form.patient_id.choices = [(pat['id'], pat['name']) for pat in patients]
        
        if request.method == 'GET':
            # Populate form with invoice data
            form.patient_id.data = invoice['patient_id']
            form.invoice_date.data = datetime.strptime(invoice['invoice_date'], '%Y-%m-%d').date()
            form.due_date.data = datetime.strptime(invoice['due_date'], '%Y-%m-%d').date()
            form.amount.data = invoice['amount']
            form.status.data = invoice['status']
            form.notes.data = invoice['notes']
        
        if form.validate_on_submit():
            # Update invoice in database
            invoice_data = {
                'patient_id': form.patient_id.data,
                'invoice_date': form.invoice_date.data.isoformat(),
                'due_date': form.due_date.data.isoformat(),
                'amount': float(form.amount.data),
                'status': form.status.data,
                'notes': form.notes.data,
                'updated_at': datetime.now().isoformat()
            }
            
            supabase_client.table('invoices').update(invoice_data).eq('id', id).execute()
            flash('Invoice updated successfully!', 'success')
            return redirect(url_for('billing.view', id=id))
            
    except Exception as e:
        flash(f'Error updating invoice: {str(e)}', 'danger')
    
    return render_template('billing/edit.html', form=form, invoice=invoice)