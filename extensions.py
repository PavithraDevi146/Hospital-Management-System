from flask_login import LoginManager
import supabase
from config import Config

# Initialize Flask-Login
login_manager = LoginManager()

supabase_client = supabase.create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_SERVICE_KEY  # Use service role instead of regular key
)