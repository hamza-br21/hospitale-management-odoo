{
    'name': 'Gestion Hospitalière',
    'version': '1.0',
    'summary': 'Advanced Hospital Management System with Analytics & Notifications',
    'description': """
        Comprehensive Hospital Management System with:
        - Patient & Doctor Management
        - Smart Appointment Scheduling with Calendar View
        - Advanced Dashboard with Real-time Statistics
        - Financial Analytics & Revenue Tracking
        - Automated Notifications (Email/SMS)
        - Department & Bed Management
        - Prescription & Billing System
        - Insurance Management
        - External API Integrations
        - Modern UI with Charts & Graphs
        - Performance Analytics & Reports
    """,
    'category': 'Healthcare',
    'author': 'HAMZA & MOHAMED',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence_data.xml',
        'data/admission_sequence.xml',
        'data/prescription_sequence.xml',
        'data/bill_sequence.xml',
        'data/cron_jobs.xml',
        'data/mail_template.xml', # Added Mail Templates
        'data/demo.xml',
        
        # Views
        'views/templates.xml',
        'views/menu_views.xml',
        'views/patient_views.xml',
        'views/doctor_views.xml',
        'views/appointment_views.xml',
        'views/department_views.xml',
        'views/dashboard_views.xml',
        'views/dashboard_advanced_views.xml',
        'views/enhanced_views.xml',
        'views/medicine_views.xml',
        'views/room_views.xml',
        'views/bed_views.xml',
        'views/admission_views.xml',
        'views/prescription_views.xml',
        'views/bill_views.xml',
        'views/insurance_views.xml',
        'views/insurance_provider_views.xml',
        'views/specialization_views.xml',
        'views/prescription_config_views.xml',

        # Reports
        'reports/prescription_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'gestion_hospitaliere/static/src/css/hospital_styles.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
