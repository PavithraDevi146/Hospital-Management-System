from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length
from extensions import supabase_client
from datetime import datetime

doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

class DoctorForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    specialty = StringField('Specialty', validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('general_medicine', 'General Medicine'),
        ('gynecology', 'Gynecology'),
        ('ophthalmology', 'Ophthalmology'),
        ('dermatology', 'Dermatology'),
        ('psychiatry', 'Psychiatry'),
        ('ent', 'ENT')
    ])
    qualification = StringField('Qualification', validators=[DataRequired()])
    experience = StringField('Experience (in years)', validators=[DataRequired()])
    bio = TextAreaField('Professional Bio', validators=[Optional()])
    submit = SubmitField('Save Doctor')

@doctors_bp.route('/')
@login_required
def list():
    try:
        # Get all doctors
        response = supabase_client.table('users').select('*').eq('role', 'doctor').execute()
        doctors = response.data if response.data else []
        return render_template('doctors/list.html', doctors=doctors)
    except Exception as e:
        flash(f'Error fetching doctors: {str(e)}', 'danger')
        return render_template('doctors/list.html', doctors=[])

@doctors_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # Only admin or manager should be able to add doctors
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to add doctors.', 'warning')
        return redirect(url_for('doctors.list'))
    
    form = DoctorForm()
    if form.validate_on_submit():
        try:
            # First, create a user account for the doctor
            # In a production environment, you might want to send them an invitation
            # or generate a temporary password
            import secrets
            temp_password = secrets.token_urlsafe(12)
            
            response = supabase_client.auth.admin.create_user({
                'email': form.email.data,
                'password': temp_password,
                'email_confirm': True
            })
            
            # Insert doctor data into users table
            doctor_data = {
                'user_id': response.user.id,
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'role': 'doctor',
                'specialty': form.specialty.data,
                'department': form.department.data,
                'qualification': form.qualification.data,
                'experience': form.experience.data,
                'bio': form.bio.data,
                'created_at': datetime.now().isoformat(),
                'created_by': current_user.id
            }
            
            supabase_client.table('users').insert(doctor_data).execute()
            
            flash(f'Doctor added successfully! Temporary password: {temp_password}', 'success')
            return redirect(url_for('doctors.list'))
        except Exception as e:
            flash(f'Error adding doctor: {str(e)}', 'danger')
    
    return render_template('doctors/add.html', form=form)

@doctors_bp.route('/view/<id>')
@login_required
def view(id):
    try:
        # Get doctor details
        response = supabase_client.table('users').select('*').eq('id', id).eq('role', 'doctor').execute()
        if response.data:
            doctor = response.data[0]
            
            # Get doctor's upcoming appointments
            appointments_response = supabase_client.table('appointments').select(
                '*, patients(name)'
            ).eq('doctor_id', id).order('date', desc=False).limit(5).execute()
            
            appointments = appointments_response.data if appointments_response.data else []
            
            return render_template('doctors/view.html', doctor=doctor, appointments=appointments)
        else:
            flash('Doctor not found.', 'warning')
            return redirect(url_for('doctors.list'))
    except Exception as e:
        flash(f'Error fetching doctor details: {str(e)}', 'danger')
        return redirect(url_for('doctors.list'))

@doctors_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to edit doctors.', 'warning')
        return redirect(url_for('doctors.list'))
    
    try:
        # Get doctor details
        response = supabase_client.table('users').select('*').eq('id', id).eq('role', 'doctor').execute()
        if not response.data:
            flash('Doctor not found.', 'warning')
            return redirect(url_for('doctors.list'))
        
        doctor = response.data[0]
        form = DoctorForm()
        
        if request.method == 'GET':
            # Populate form with doctor data
            form.name.data = doctor.get('name')
            form.email.data = doctor.get('email')
            form.phone.data = doctor.get('phone')
            form.specialty.data = doctor.get('specialty')
            form.department.data = doctor.get('department')
            form.qualification.data = doctor.get('qualification')
            form.experience.data = doctor.get('experience')
            form.bio.data = doctor.get('bio')
        
        if form.validate_on_submit():
            try:
                # Update doctor in database
                doctor_data = {
                    'name': form.name.data,
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'specialty': form.specialty.data,
                    'department': form.department.data,
                    'qualification': form.qualification.data,
                    'experience': form.experience.data,
                    'bio': form.bio.data,
                    'updated_at': datetime.now().isoformat()
                }
                
                supabase_client.table('users').update(doctor_data).eq('id', id).execute()
                flash('Doctor information updated successfully!', 'success')
                return redirect(url_for('doctors.view', id=id))
            except Exception as e:
                flash(f'Error updating doctor: {str(e)}', 'danger')
        
        return render_template('doctors/edit.html', form=form, doctor=doctor)
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'danger')
        return redirect(url_for('doctors.list'))