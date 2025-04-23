from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from extensions import supabase_client
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional()])
    submit = SubmitField('Update Profile')

class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

@settings_bp.route('/')
@login_required
def index():
    return render_template('settings/index.html')

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm()
    password_form = PasswordForm()
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        # Handle profile update
        if form_type == 'profile' and profile_form.validate_on_submit():
            try:
                # Update user data
                user_data = {
                    'name': profile_form.name.data,
                    'phone': profile_form.phone.data,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Email is a special case since it needs to be updated in auth.users as well
                if profile_form.email.data != current_user.email:
                    # Update email in both tables
                    supabase_client.auth.admin.update_user_by_id(
                        user_id=current_user.get_id(),
                        attributes={'email': profile_form.email.data}
                    )
                    user_data['email'] = profile_form.email.data
                
                # Update the user record
                supabase_client.table('users').update(user_data).eq('id', current_user.get_id()).execute()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('settings.profile'))
            
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'danger')
        
        # Handle password change
        elif form_type == 'password' and password_form.validate_on_submit():
            try:
                # Verify current password
                response = supabase_client.auth.sign_in_with_password(
                    credentials={"email": current_user.email, "password": password_form.current_password.data}
                )
                
                if response.user:
                    # Update password
                    supabase_client.auth.admin.update_user_by_id(
                        user_id=current_user.get_id(),
                        attributes={'password': password_form.new_password.data}
                    )
                    flash('Password changed successfully!', 'success')
                else:
                    flash('Current password is incorrect.', 'danger')
                
                return redirect(url_for('settings.profile'))
            
            except Exception as e:
                flash(f'Error changing password: {str(e)}', 'danger')
    
    # For GET requests, populate the profile form
    if request.method == 'GET':
        try:
            response = supabase_client.table('users').select('*').eq('id', current_user.get_id()).execute()
            if response.data:
                user = response.data[0]
                profile_form.name.data = user.get('name')
                profile_form.email.data = user.get('email')
                profile_form.phone.data = user.get('phone')
        except Exception as e:
            flash(f'Error loading profile data: {str(e)}', 'danger')
    
    return render_template('settings/profile.html', profile_form=profile_form, password_form=password_form)

@settings_bp.route('/system', methods=['GET', 'POST'])
@login_required
def system():
    # Only admin users should access system settings
    if current_user.role != 'admin':
        flash('You do not have permission to access system settings.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    return render_template('settings/system.html')