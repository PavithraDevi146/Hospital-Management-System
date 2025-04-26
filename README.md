# Hospital Management System (HMGMT)

A comprehensive Flask-based hospital management system with patient records, appointments, billing, and more.

![Hospital Management System](https://via.placeholder.com/800x400?text=Hospital+Management+System)
## License and Copyright

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 PAVITHRA DEVI M or NoCorps.org All rights reserved.

The Hospital Management System name and logo are trademarks of Your Name or Organization.


## Features

- **User Authentication**: Secure login and role-based access control (Admin, Doctor, Staff)
- **Dashboard**: Overview of hospital activities and statistics
- **Patient Management**: Add, view, edit patient records with medical history
- **Doctor Management**: Manage doctor profiles with specialties and departments
- **Appointment Scheduling**: Schedule, reschedule, and track patient appointments
- **Medical Records**: Create and manage detailed medical records with file attachments
- **Billing System**: Generate invoices and track payment status
- **Settings**: User profile management and system configuration

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL with Supabase
- **Authentication**: Supabase Auth
- **Frontend**: HTML, CSS, Bootstrap 5, jQuery
- **Templating**: Jinja2
- **Forms**: Flask-WTF

## Setup and Installation

### Prerequisites

- Python 3.8+
- PostgreSQL or Supabase account
- pip (Python package manager)

### Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hospital-management.git
   cd hospital-management
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with the following variables:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

### Database Setup

1. Create a new project in Supabase

2. Run the following SQL to set up your database schema (or use Supabase UI):

```sql
-- Create tables for the hospital management system
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL,
    specialty VARCHAR(100),
    department VARCHAR(100),
    qualification TEXT,
    experience INTEGER,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE public.patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    address TEXT,
    medical_history TEXT,
    allergies TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES auth.users(id)
);

CREATE TABLE public.appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES public.patients(id),
    doctor_id UUID REFERENCES auth.users(id),
    date DATE NOT NULL,
    time TIME NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES auth.users(id)
);

CREATE TABLE public.medical_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES public.patients(id),
    doctor_id UUID REFERENCES auth.users(id),
    record_date DATE NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment TEXT NOT NULL,
    notes TEXT,
    attachment_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES auth.users(id)
);

CREATE TABLE public.invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES public.patients(id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

3. Set up row-level security policies in Supabase:

```sql
-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Allow admins full access" ON public.users 
    USING (auth.uid() IN (SELECT id FROM public.users WHERE role = 'admin'))
    WITH CHECK (auth.uid() IN (SELECT id FROM public.users WHERE role = 'admin'));

CREATE POLICY "Allow users to read their own data" ON public.users 
    FOR SELECT USING (auth.uid() = id);

-- Create policies for patients table
CREATE POLICY "Allow all authenticated users to read patients" ON public.patients 
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.users));

CREATE POLICY "Allow staff and admins to create patients" ON public.patients 
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.users WHERE role IN ('admin', 'staff')));

CREATE POLICY "Allow staff and admins to update patients" ON public.patients 
    FOR UPDATE USING (auth.uid() IN (SELECT id FROM public.users WHERE role IN ('admin', 'staff')));

-- Similar policies for other tables...
```

4. Create a storage bucket for medical record attachments:

```
Storage Bucket Name: medical-attachments
Public Access: Restricted
File Size Limit: 10MB
Allowed MIME Types: image/jpeg,image/png,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

### Running the Application

1. Start the Flask application:
   ```
   flask run
   ```
   or
   ```
   python app.py
   ```

2. Open a web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Login with admin credentials:
   - **Email**: admin@example.com
   - **Password**: admin123 (change this immediately in production)

## Project Structure

```
hmgmt/
├── app.py              # Application entry point
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not in version control)
├── routes/             # Application routes
│   ├── appointments.py
│   ├── auth.py
│   ├── billing.py
│   ├── dashboard.py
│   ├── doctors.py
│   ├── medical_records.py
│   ├── patients.py
│   └── settings.py
├── static/             # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── scripts.js
│   └── uploads/
└── templates/          # HTML templates
    ├── appointments/
    │   ├── edit.html
    │   ├── list.html
    │   ├── schedule.html
    │   └── view.html
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── billing/
    │   ├── create.html
    │   ├── edit.html
    │   ├── list.html
    │   └── view.html
    ├── dashboard/
    │   └── index.html
    ├── doctors/
    │   ├── add.html
    │   ├── edit.html
    │   ├── list.html
    │   └── view.html
    ├── medical_records/
    │   ├── add.html
    │   ├── edit.html
    │   ├── list.html
    │   └── view.html
    ├── patients/
    │   ├── add.html
    │   ├── edit.html
    │   ├── list.html
    │   └── view.html
    └── settings/
        ├── index.html
        ├── profile.html
        └── system.html
```

## Default User Accounts

The application comes with default user accounts for testing:

1. **Admin User**
   - Email: admin@example.com
   - Password: admin123
   - Role: admin

2. **Doctor User**
   - Email: doctor@example.com
   - Password: doctor123
   - Role: doctor

3. **Staff User**
   - Email: staff@example.com
   - Password: staff123
   - Role: staff

## User Roles and Permissions

- **Administrator**:
  - Full access to all features and settings
  - Can add/edit/delete users, including doctors
  - Can manage system settings
  - Can access all patient records, appointments, and billing information
  
- **Doctor**:
  - Access to assigned patient records and medical history
  - Can view and update their own appointments
  - Can create and edit medical records
  - Can view billing information related to their patients
  - Limited access to system settings (profile only)

- **Staff**:
  - Can register and manage patients
  - Can schedule and manage appointments
  - Can create and manage invoices
  - Can view medical records but not create/edit them
  - Limited access to system settings (profile only)

## Key Functionality Details

### Dashboard

The dashboard provides an at-a-glance overview of key metrics including:
- Total patients
- Today's appointments
- Upcoming appointments
- Recent medical records
- Outstanding invoices
- Doctor availability

### Patient Management

- Add new patients with detailed medical history
- Edit patient information
- View patient history including past appointments and medical records
- Schedule appointments directly from patient profile

### Appointment Scheduling

- Schedule appointments with specific doctors
- Filter appointments by date, doctor, or status
- Manage appointment statuses (scheduled, confirmed, completed, cancelled)
- Appointment calendar view

### Medical Records

- Create detailed medical records with diagnosis, treatment plans
- Attach files to medical records (X-rays, lab reports, etc.)
- Organize records by type and date
- Search and filter records

### Billing System

- Create invoices linked to patients
- Track payment status
- Payment history
- Generate printable invoices

## Security Features

- Password hashing using Supabase Auth
- CSRF protection with Flask-WTF
- Role-based access control
- Session management and timeouts
- Input validation and sanitization
- Database security with prepared statements
- HTTPS support for production deployment
- File upload validation and restrictions

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## Troubleshooting

Common issues and their solutions:

1. **Database Connection Issues**:
   - Verify your Supabase URL and API key in the .env file
   - Check if your IP is allowed in Supabase settings

2. **Authentication Problems**:
   - Clear browser cookies and try logging in again
   - Reset password through Supabase Auth dashboard if needed

3. **Missing Templates**:
   - Ensure all template files exist in their respective directories
   - Check for typos in template references

4. **File Upload Issues**:
   - Verify storage bucket permissions in Supabase
   - Check file size limits and allowed MIME types

## Future Development Plans

- Patient portal for self-service appointment booking
- Integrated telehealth consultation system
- Laboratory test result integration
- Pharmacy management
- Insurance claim processing
- Mobile application for doctors and patients
- Advanced reporting and analytics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask framework documentation
- Bootstrap 5 for responsive UI design
- Supabase for authentication and database services
- Flask-WTF for form handling and CSRF protection
- The open-source community for inspiration and guidance
