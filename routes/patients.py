from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional
from extensions import supabase_client
from datetime import datetime  # Add this import

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

class PatientForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ])
    address = TextAreaField('Address', validators=[Optional()])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    submit = SubmitField('Save Patient')

@patients_bp.route('/')
@login_required
def list():
    try:
        # Get all patients
        response = supabase_client.table('patients').select('*').execute()
        patients = response.data if response.data else []
        return render_template('patients/list.html', patients=patients)
    except Exception as e:
        flash(f'Error fetching patients: {str(e)}', 'danger')
        return render_template('patients/list.html', patients=[])

@patients_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # Debugging code can stay
    print("Current user type:", type(current_user))
    try:
        current_user.debug_info()
    except Exception as e:
        print(f"Error accessing current_user: {e}")

    form = PatientForm()
    if form.validate_on_submit():
        try:
            # Keep this section as is
            patient_data = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'date_of_birth': form.date_of_birth.data.isoformat(),
                'gender': form.gender.data,
                'blood_group': form.blood_group.data,
                'address': form.address.data,
                'medical_history': form.medical_history.data,
                'registered_by': current_user.get_id()  # This line is correct
            }
            
            response = supabase_client.table('patients').insert(patient_data).execute()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('patients.list'))
        except Exception as e:
            flash(f'Error adding patient: {str(e)}', 'danger')
    
    return render_template('patients/add.html', form=form)

@patients_bp.route('/view/<id>')
@login_required
def view(id):
    try:
        # Get patient details
        response = supabase_client.table('patients').select('*').eq('id', id).execute()
        if response.data:
            patient = response.data[0]
            return render_template('patients/view.html', patient=patient)
        else:
            flash('Patient not found.', 'warning')
            return redirect(url_for('patients.list'))
    except Exception as e:
        flash(f'Error fetching patient details: {str(e)}', 'danger')
        return redirect(url_for('patients.list'))

@patients_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    try:
        # Get patient details
        response = supabase_client.table('patients').select('*').eq('id', id).execute()
        if not response.data:
            flash('Patient not found.', 'warning')
            return redirect(url_for('patients.list'))
        
        patient = response.data[0]
        form = PatientForm()
        
        if request.method == 'GET':
            # Populate form with patient data
            form.name.data = patient['name']
            form.email.data = patient['email']
            form.phone.data = patient['phone']
            
            # Handle date format
            if patient['date_of_birth']:
                form.date_of_birth.data = datetime.strptime(patient['date_of_birth'], '%Y-%m-%d').date()
                
            form.gender.data = patient['gender']
            form.blood_group.data = patient['blood_group']
            form.address.data = patient['address']
            form.medical_history.data = patient['medical_history']
        
        if form.validate_on_submit():
            try:
                # Update patient in database
                patient_data = {
                    'name': form.name.data,
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'date_of_birth': form.date_of_birth.data.isoformat(),
                    'gender': form.gender.data,
                    'blood_group': form.blood_group.data,
                    'address': form.address.data,
                    'medical_history': form.medical_history.data,
                    'updated_at': datetime.now().isoformat()
                }
                
                supabase_client.table('patients').update(patient_data).eq('id', id).execute()
                flash('Patient updated successfully!', 'success')
                return redirect(url_for('patients.view', id=id))
            except Exception as e:
                flash(f'Error updating patient: {str(e)}', 'danger')
        
        return render_template('patients/edit.html', form=form, patient=patient)
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'danger')
        return redirect(url_for('patients.list'))