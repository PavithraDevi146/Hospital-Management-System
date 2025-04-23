from flask_login import UserMixin
from extensions import supabase_client

class User(UserMixin):
    def __init__(self, id, email, name, role, is_active=True):
        self._id = id  # Use _id as private attribute
        self.email = email
        self.name = name
        self.role = role
        self._is_active = is_active  # Use _is_active as private attribute
    
    @property
    def id(self):
        return self._id
    
    def get_id(self):
        return self._id
    
    # Don't override is_authenticated or is_anonymous as properties
    # Let UserMixin handle these
    
    @property
    def is_active(self):
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @staticmethod
    def get_by_id(user_id):
        try:
            # Get user from Supabase
            response = supabase_client.table('users').select('*').eq('id', user_id).execute()
            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    name=user_data['name'],
                    role=user_data.get('role', 'user')
                )
        except Exception as e:
            print(f"Error fetching user: {e}")
        return None
    
    def debug_info(self):
        """Print debug information about user attributes"""
        print(f"User debug info:")
        print(f"_id: {self._id}")
        print(f"id property: {self.id}")
        print(f"get_id(): {self.get_id()}")
        print(f"email: {self.email}")
        print(f"role: {self.role}")

# current_user.debug_info()  # Before trying to access current_user.id