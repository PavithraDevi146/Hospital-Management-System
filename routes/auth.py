from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import login_user, logout_user, current_user
from extensions import supabase_client
from models import User  # Import from models instead of app

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('staff', 'Staff')
    ], default='staff')
    submit = SubmitField('Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Authenticate with Supabase
            response = supabase_client.auth.sign_in_with_password({
                'email': form.email.data,
                'password': form.password.data
            })
            
            # Get user data from the users table
            user_response = supabase_client.table('users').select('*').eq('email', form.email.data).execute()
            
            if user_response.data:
                user_data = user_response.data[0]
                
                # Create a User object from models.py
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    name=user_data['name'],
                    role=user_data.get('role', 'user'),  # Add default value
                    is_active=True
                )
                
                # Log in the user with Flask-Login
                login_user(user, remember=form.remember_me.data)
                
                flash('Logged in successfully.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                flash('User not found in database.', 'danger')
        except Exception as e:
            error_message = str(e)
            if "Email not confirmed" in error_message:
                flash('Please confirm your email address before logging in. Check your inbox for a confirmation link.', 'warning')
            else:
                flash(f'Login error: {error_message}', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            check = supabase_client.table('users').select('*').eq('email', form.email.data).execute()
            if check.data:
                flash('Email already registered.', 'danger')
                return render_template('auth/register.html', form=form)
            
            # Register with Supabase Auth
            auth_response = supabase_client.auth.sign_up({
                'email': form.email.data,
                'password': form.password.data
            })
            
            # Get the user ID from auth response
            user_id = auth_response.user.id
            
            # Insert user data into users table
            user_data = {
                'user_id': user_id,
                'email': form.email.data,
                'name': form.name.data,
                'role': form.role.data
            }
            
            supabase_client.table('users').insert(user_data).execute()
            
            flash('Registration successful! Please check your email to confirm your account before logging in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    try:
        supabase_client.auth.sign_out()
    except:
        pass
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))