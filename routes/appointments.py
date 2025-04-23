from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional
from datetime import datetime, time
from extensions import supabase_client

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

class AppointmentForm(FlaskForm):
    patient_id = HiddenField('Patient ID')
    doctor_id = SelectField('Doctor', validators=[DataRequired()], coerce=str)
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    reason = StringField('Reason for Visit', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Appointment')

@appointments_bp.route('/')
@login_required
def list():
    try:
        # Get all appointments with patient and doctor information
        response = supabase_client.table('appointments').select('*, patients(name), users!doctor_id(name)').execute()
        appointments = response.data if response.data else []
        return render_template('appointments/list.html', appointments=appointments)
    except Exception as e:
        flash(f'Error fetching appointments: {str(e)}', 'danger')
        return render_template('appointments/list.html', appointments=[])

@appointments_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    form = AppointmentForm()
    
    # Populate the doctor dropdown
    try:
        doctors_response = supabase_client.table('users').select('id, name').eq('role', 'doctor').execute()
        doctors = doctors_response.data if doctors_response.data else []
        form.doctor_id.choices = [(doc['id'], doc['name']) for doc in doctors]
    except Exception as e:
        flash(f'Error fetching doctors: {str(e)}', 'danger')
        form.doctor_id.choices = []
    
    # If coming from patient view, pre-populate patient_id
    if request.args.get('patient_id'):
        form.patient_id.data = request.args.get('patient_id')
    
    if form.validate_on_submit():
        try:
            # Format time and date for database
            appointment_time = form.time.data.strftime('%H:%M')
            appointment_date = form.date.data.isoformat()
            
            # Insert appointment into database
            appointment_data = {
                'patient_id': form.patient_id.data,
                'doctor_id': form.doctor_id.data,
                'date': appointment_date,
                'time': appointment_time,
                'reason': form.reason.data,
                'status': form.status.data,
                'notes': form.notes.data,
                'created_by': current_user.get_id()
            }
            
            response = supabase_client.table('appointments').insert(appointment_data).execute()
            flash('Appointment scheduled successfully!', 'success')
            
            # If this was scheduled from a patient profile, return there
            if form.patient_id.data:
                return redirect(url_for('patients.view', id=form.patient_id.data))
            else:
                return redirect(url_for('appointments.list'))
                
        except Exception as e:
            flash(f'Error scheduling appointment: {str(e)}', 'danger')
    
    # If patient_id is provided, fetch patient details for the form
    patient = None
    if form.patient_id.data:
        try:
            patient_response = supabase_client.table('patients').select('*').eq('id', form.patient_id.data).execute()
            if patient_response.data:
                patient = patient_response.data[0]
        except Exception as e:
            flash(f'Error fetching patient details: {str(e)}', 'warning')
    
    return render_template('appointments/schedule.html', form=form, patient=patient)

@appointments_bp.route('/view/<id>')
@login_required
def view(id):
    try:
        # Get appointment details with related patient and doctor info
        response = supabase_client.table('appointments').select(
            '*, patients(name, email, phone), users!doctor_id(name)'
        ).eq('id', id).execute()
        
        if response.data:
            appointment = response.data[0]
            return render_template('appointments/view.html', appointment=appointment)
        else:
            flash('Appointment not found.', 'warning')
            return redirect(url_for('appointments.list'))
    except Exception as e:
        flash(f'Error fetching appointment details: {str(e)}', 'danger')
        return redirect(url_for('appointments.list'))

@appointments_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    try:
        # Get appointment details
        response = supabase_client.table('appointments').select('*').eq('id', id).execute()
        if not response.data:
            flash('Appointment not found.', 'warning')
            return redirect(url_for('appointments.list'))
        
        appointment = response.data[0]
        form = AppointmentForm()
        
        # Populate the doctor dropdown
        doctors_response = supabase_client.table('users').select('id, name').eq('role', 'doctor').execute()
        doctors = doctors_response.data if doctors_response.data else []
        form.doctor_id.choices = [(doc['id'], doc['name']) for doc in doctors]
        
        if request.method == 'GET':
            # Populate form with appointment data
            form.patient_id.data = appointment['patient_id']
            form.doctor_id.data = appointment['doctor_id']
            form.date.data = datetime.strptime(appointment['date'], '%Y-%m-%d').date()
            
            # FIX: Updated time parsing to handle seconds format (HH:MM:SS)
            try:
                # First try with seconds format
                form.time.data = datetime.strptime(appointment['time'], '%H:%M:%S').time()
            except ValueError:
                # Fall back to no-seconds format if the first attempt fails
                form.time.data = datetime.strptime(appointment['time'], '%H:%M').time()
                
            form.reason.data = appointment['reason']
            form.status.data = appointment['status']
            form.notes.data = appointment['notes']
        
        if form.validate_on_submit():
            try:
                # Format time and date for database
                appointment_time = form.time.data.strftime('%H:%M')
                appointment_date = form.date.data.isoformat()
                
                # Update appointment in database
                appointment_data = {
                    'doctor_id': form.doctor_id.data,
                    'date': appointment_date,
                    'time': appointment_time,
                    'reason': form.reason.data,
                    'status': form.status.data,
                    'notes': form.notes.data,
                    'updated_at': datetime.now().isoformat()
                }
                
                supabase_client.table('appointments').update(appointment_data).eq('id', id).execute()
                flash('Appointment updated successfully!', 'success')
                return redirect(url_for('appointments.view', id=id))
            except Exception as e:
                flash(f'Error updating appointment: {str(e)}', 'danger')
        
        # Get patient details for display in the form
        patient = None
        if form.patient_id.data:
            patient_response = supabase_client.table('patients').select('*').eq('id', form.patient_id.data).execute()
            if patient_response.data:
                patient = patient_response.data[0]
        
        return render_template('appointments/edit.html', form=form, appointment=appointment, patient=patient)
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'danger')
        return redirect(url_for('appointments.list'))

@appointments_bp.route('/cancel/<id>')
@login_required
def cancel(id):
    try:
        # Update appointment status to cancelled
        supabase_client.table('appointments').update({'status': 'cancelled'}).eq('id', id).execute()
        flash('Appointment cancelled successfully!', 'success')
        return redirect(url_for('appointments.view', id=id))
    except Exception as e:
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
        return redirect(url_for('appointments.view', id=id))