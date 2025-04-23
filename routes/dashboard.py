from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
# from app import supabase_client
from extensions import supabase_client

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Fetch statistics for the dashboard
    try:
        # Get patient count
        patients_response = supabase_client.table('patients').select('count', count='exact').execute()
        patient_count = patients_response.count if hasattr(patients_response, 'count') else 0
        
        # Get appointment count
        appointments_response = supabase_client.table('appointments').select('count', count='exact').execute()
        appointment_count = appointments_response.count if hasattr(appointments_response, 'count') else 0
        
        # Get today's appointments
        import datetime
        today = datetime.date.today().isoformat()
        today_appointments_response = supabase_client.table('appointments').select('count', count='exact').eq('date', today).execute()
        today_appointment_count = today_appointments_response.count if hasattr(today_appointments_response, 'count') else 0
        
        # Get doctor count
        doctors_response = supabase_client.table('users').select('count', count='exact').eq('role', 'doctor').execute()
        doctor_count = doctors_response.count if hasattr(doctors_response, 'count') else 0
        
        return render_template('dashboard/index.html', 
                              patient_count=patient_count,
                              appointment_count=appointment_count,
                              today_appointment_count=today_appointment_count,
                              doctor_count=doctor_count)
    except Exception as e:
        flash(f'Error loading dashboard data: {str(e)}', 'danger')
        return render_template('dashboard/index.html', error=True)