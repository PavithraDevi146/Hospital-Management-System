from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from extensions import supabase_client

medical_records_bp = Blueprint('medical_records', __name__, url_prefix='/medical-records')

# Form class for medical records
class MedicalRecordForm(FlaskForm):
    patient_id = SelectField('Patient', validators=[DataRequired()], coerce=str)
    doctor_id = SelectField('Doctor', validators=[DataRequired()], coerce=str)
    record_type = SelectField('Record Type', choices=[
        ('consultation', 'Consultation'),
        ('lab_test', 'Laboratory Test'),
        ('prescription', 'Prescription'),
        ('imaging', 'Imaging'),
        ('surgery', 'Surgery'),
        ('discharge', 'Discharge Summary'),
        ('other', 'Other')
    ])
    diagnosis = StringField('Diagnosis', validators=[DataRequired()])
    treatment = TextAreaField('Treatment', validators=[DataRequired()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    record_date = DateField('Record Date', validators=[DataRequired()], format='%Y-%m-%d')
    attachments = FileField('Attachments', validators=[
        FileAllowed(['jpg', 'png', 'pdf', 'doc', 'docx'], 'Images and documents only!')
    ])
    submit = SubmitField('Save Record')

@medical_records_bp.route('/')
@login_required
def list():
    try:
        # Get all medical records with patient and doctor information
        response = supabase_client.table('medical_records').select(
            '*, patients(name), users!doctor_id(name)'
        ).order('record_date', desc=True).execute()
        
        records = response.data if response.data else []
        return render_template('medical_records/list.html', records=records)
    except Exception as e:
        flash(f'Error fetching medical records: {str(e)}', 'danger')
        return render_template('medical_records/list.html', records=[])

@medical_records_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = MedicalRecordForm()
    
    # Check if we're coming from a patient profile and retrieve patient info
    patient = None
    if request.args.get('patient_id'):
        try:
            patient_id = request.args.get('patient_id')
            # Set the patient_id in the form
            form.patient_id.data = patient_id
            
            # Get patient details for display
            patient_response = supabase_client.table('patients').select('*').eq('id', patient_id).execute()
            if patient_response.data:
                patient = patient_response.data[0]
        except Exception as e:
            flash(f'Error retrieving patient information: {str(e)}', 'warning')
    
    # Populate the doctor dropdown
    try:
        doctors_response = supabase_client.table('users').select('id, name').eq('role', 'doctor').execute()
        doctors = doctors_response.data if doctors_response.data else []
        form.doctor_id.choices = [(doc['id'], doc['name']) for doc in doctors]
    except Exception as e:
        flash(f'Error fetching doctors: {str(e)}', 'danger')
        form.doctor_id.choices = []
    
    # Populate the patient dropdown
    try:
        patients_response = supabase_client.table('patients').select('id, name').execute()
        patients = patients_response.data if patients_response.data else []
        form.patient_id.choices = [(pat['id'], pat['name']) for pat in patients]
    except Exception as e:
        flash(f'Error fetching patients: {str(e)}', 'danger')
        form.patient_id.choices = []
    
    if form.validate_on_submit():
        try:
            # Print debugging info
            print(f"Current user ID: {current_user.get_id()}")
            print(f"User role: {current_user.role}")
            
            # Handle file upload
            attachment_url = None
            if form.attachments.data:
                file_data = form.attachments.data
                filename = secure_filename(file_data.filename)
                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Save to Supabase storage
                with file_data.stream as file_stream:
                    supabase_client.storage.from_('medical-attachments').upload(
                        unique_filename,
                        file_stream.read()
                    )
                
                # Get the public URL
                attachment_url = supabase_client.storage.from_('medical-attachments').get_public_url(unique_filename)
            
            # Insert medical record into database
            record_data = {
                'patient_id': form.patient_id.data,
                'doctor_id': form.doctor_id.data,
                'record_type': form.record_type.data,
                'diagnosis': form.diagnosis.data,
                'treatment': form.treatment.data,
                'notes': form.notes.data,
                'record_date': form.record_date.data.isoformat(),
                'attachment_url': attachment_url,
                'created_by': current_user.get_id(),
                'created_at': datetime.now().isoformat()
            }
            
            # Add more detailed error handling
            try:
                print("Attempting to insert record with data:", record_data)
                response = supabase_client.table('medical_records').insert(record_data).execute()
                print("Insert response:", response)
                flash('Medical record added successfully!', 'success')
                
                # If this was added from a patient profile, return there
                if form.patient_id.data:
                    return redirect(url_for('medical_records.patient_records', patient_id=form.patient_id.data))
                else:
                    return redirect(url_for('medical_records.list'))
            except Exception as e:
                # More detailed error logging
                flash(f'Database error: {str(e)}', 'danger')
                print(f"Supabase error details: {e}")
                
        except Exception as e:
            flash(f'Error adding medical record: {str(e)}', 'danger')
    
    return render_template('medical_records/add.html', form=form, patient=patient)

@medical_records_bp.route('/view/<id>')
@login_required
def view(id):
    try:
        # Get medical record details with related patient and doctor info
        response = supabase_client.table('medical_records').select(
            '*, patients(name, email, phone), users!doctor_id(name)'
        ).eq('id', id).execute()
        
        if response.data:
            record = response.data[0]
            return render_template('medical_records/view.html', record=record)
        else:
            flash('Medical record not found.', 'warning')
            return redirect(url_for('medical_records.list'))
    except Exception as e:
        flash(f'Error fetching medical record details: {str(e)}', 'danger')
        return redirect(url_for('medical_records.list'))

@medical_records_bp.route('/patient/<patient_id>')
@login_required
def patient_records(patient_id):
    try:
        # Get patient details
        patient_response = supabase_client.table('patients').select('*').eq('id', patient_id).execute()
        if not patient_response.data:
            flash('Patient not found.', 'warning')
            return redirect(url_for('patients.list'))
            
        patient = patient_response.data[0]
        
        # Get all medical records for this patient
        records_response = supabase_client.table('medical_records').select(
            '*, users!doctor_id(name)'
        ).eq('patient_id', patient_id).order('record_date', desc=True).execute()
        
        records = records_response.data if records_response.data else []
        
        return render_template('medical_records/patient_records.html', 
                              patient=patient, 
                              records=records)
    except Exception as e:
        flash(f'Error fetching patient medical records: {str(e)}', 'danger')
        return redirect(url_for('patients.list'))

@medical_records_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    try:
        # Get record details
        response = supabase_client.table('medical_records').select('*').eq('id', id).execute()
        if not response.data:
            flash('Medical record not found.', 'warning')
            return redirect(url_for('medical_records.list'))
            
        record = response.data[0]
        form = MedicalRecordForm()
        
        # Populate the doctor dropdown
        doctors_response = supabase_client.table('users').select('id, name').eq('role', 'doctor').execute()
        doctors = doctors_response.data if doctors_response.data else []
        form.doctor_id.choices = [(doc['id'], doc['name']) for doc in doctors]
        
        # Populate the patient dropdown
        patients_response = supabase_client.table('patients').select('id, name').execute()
        patients = patients_response.data if patients_response.data else []
        form.patient_id.choices = [(pat['id'], pat['name']) for pat in patients]
        
        if request.method == 'GET':
            # Populate form with record data
            form.patient_id.data = record['patient_id']
            form.doctor_id.data = record['doctor_id']
            form.record_type.data = record['record_type']
            form.diagnosis.data = record['diagnosis']
            form.treatment.data = record['treatment']
            form.notes.data = record['notes']
            
            # Handle date format
            if record['record_date']:
                form.record_date.data = datetime.strptime(record['record_date'], '%Y-%m-%d').date()
        
        if form.validate_on_submit():
            try:
                # Handle file upload if new one is provided
                attachment_url = record['attachment_url']  # Keep existing URL by default
                if form.attachments.data:
                    file_data = form.attachments.data
                    filename = secure_filename(file_data.filename)
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Save to Supabase storage
                    with file_data.stream as file_stream:
                        supabase_client.storage.from_('medical-attachments').upload(
                            unique_filename,
                            file_stream.read()
                        )
                    
                    # Get the public URL
                    attachment_url = supabase_client.storage.from_('medical-attachments').get_public_url(unique_filename)
                
                # Update medical record in database
                record_data = {
                    'doctor_id': form.doctor_id.data,
                    'record_type': form.record_type.data,
                    'diagnosis': form.diagnosis.data,
                    'treatment': form.treatment.data,
                    'notes': form.notes.data,
                    'record_date': form.record_date.data.isoformat(),
                    'attachment_url': attachment_url,
                    'updated_by': current_user.get_id(),
                    'updated_at': datetime.now().isoformat()
                }
                
                supabase_client.table('medical_records').update(record_data).eq('id', id).execute()
                flash('Medical record updated successfully!', 'success')
                return redirect(url_for('medical_records.view', id=id))
            except Exception as e:
                flash(f'Error updating medical record: {str(e)}', 'danger')
        
        return render_template('medical_records/add.html', form=form, record=record, is_edit=True)
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'danger')
        return redirect(url_for('medical_records.list'))

@medical_records_bp.route('/delete/<id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'doctor']:
        flash('You do not have permission to delete medical records.', 'warning')
        return redirect(url_for('medical_records.list'))
        
    try:
        # Get the record to check if there's an attachment to delete
        response = supabase_client.table('medical_records').select('*').eq('id', id).execute()
        if response.data:
            record = response.data[0]
            
            # Delete the attachment if exists
            if record.get('attachment_url'):
                # Extract filename from URL
                filename = os.path.basename(record['attachment_url'])
                try:
                    supabase_client.storage.from_('medical-attachments').remove(filename)
                except:
                    # If file doesn't exist or some other error, continue anyway
                    pass
            
            # Delete the record
            supabase_client.table('medical_records').delete().eq('id', id).execute()
            flash('Medical record deleted successfully!', 'success')
        else:
            flash('Medical record not found.', 'warning')
            
        # If we have a patient_id in query params, return to their records
        if request.args.get('patient_id'):
            return redirect(url_for('medical_records.patient_records', patient_id=request.args.get('patient_id')))
        else:
            return redirect(url_for('medical_records.list'))
    except Exception as e:
        flash(f'Error deleting medical record: {str(e)}', 'danger')
        return redirect(url_for('medical_records.list'))