# Hospital Management System (HMGMT)


from flask import Flask, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from config import Config
from extensions import login_manager, supabase_client
from models import User

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions with the app
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Import and register blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.appointments import appointments_bp
from routes.doctors import doctors_bp
from routes.medical_records import medical_records_bp
from routes.billing import billing_bp  # New module
from routes.settings import settings_bp  # New module

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(patients_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(doctors_bp)
app.register_blueprint(medical_records_bp)
app.register_blueprint(billing_bp)  # Register new module
app.register_blueprint(settings_bp)  # Register new module

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)