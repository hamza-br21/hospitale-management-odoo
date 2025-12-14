from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HospitalDashboard(models.TransientModel):
    _name = 'hospital.dashboard'
    _description = 'Hospital Dashboard Statistics'

    # KPI Fields
    total_patients = fields.Integer(string='Total Patients', compute='_compute_statistics')
    total_doctors = fields.Integer(string='Total Doctors', compute='_compute_statistics')
    total_appointments_today = fields.Integer(string='Today Appointments', compute='_compute_statistics')
    total_admissions_active = fields.Integer(string='Active Admissions', compute='_compute_statistics')
    total_revenue_month = fields.Float(string='Monthly Revenue', compute='_compute_statistics')
    total_pending_bills = fields.Integer(string='Pending Bills', compute='_compute_statistics')
    bed_occupancy_rate = fields.Float(string='Bed Occupancy %', compute='_compute_statistics')
    
    # Trend Data
    patient_growth_rate = fields.Float(string='Patient Growth %', compute='_compute_statistics')
    appointment_completion_rate = fields.Float(string='Appointment Completion %', compute='_compute_statistics')
    average_bill_amount = fields.Float(string='Avg Bill Amount', compute='_compute_statistics')
    
    # Date filters
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='To Date', default=fields.Date.today)

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        for rec in self:
            # Total active patients
            rec.total_patients = self.env['hospital.patient'].search_count([('active', '=', True)])
            
            # Total active doctors
            rec.total_doctors = self.env['hospital.doctor'].search_count([('active', '=', True)])
            
            # Today's appointments
            today = fields.Date.today()
            rec.total_appointments_today = self.env['hospital.appointment'].search_count([
                ('date_appointment', '>=', today),
                ('date_appointment', '<', today + timedelta(days=1)),
                ('state', '!=', 'cancel')
            ])
            
            # Active admissions
            rec.total_admissions_active = self.env['hospital.admission'].search_count([
                ('state', '=', 'admitted')
            ])
            
            # Monthly revenue from paid bills
            first_day_month = today.replace(day=1)
            bills = self.env['hospital.bill'].search([
                ('date_bill', '>=', first_day_month),
                ('date_bill', '<=', today),
                ('state', '=', 'paid')
            ])
            rec.total_revenue_month = sum(bills.mapped('total_amount'))
            
            # Pending bills
            rec.total_pending_bills = self.env['hospital.bill'].search_count([
                ('state', '=', 'draft')
            ])
            
            # Bed occupancy rate
            total_beds = self.env['hospital.bed'].search_count([('active', '=', True)])
            occupied_beds = self.env['hospital.bed'].search_count([
                ('active', '=', True),
                ('state', '=', 'occupied')
            ])
            rec.bed_occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            # Patient growth rate (last 30 days vs previous 30 days)
            thirty_days_ago = today - timedelta(days=30)
            sixty_days_ago = today - timedelta(days=60)
            
            recent_patients = self.env['hospital.patient'].search_count([
                ('create_date', '>=', thirty_days_ago),
                ('create_date', '<=', today)
            ])
            previous_patients = self.env['hospital.patient'].search_count([
                ('create_date', '>=', sixty_days_ago),
                ('create_date', '<', thirty_days_ago)
            ])
            
            if previous_patients > 0:
                rec.patient_growth_rate = ((recent_patients - previous_patients) / previous_patients) * 100
            else:
                rec.patient_growth_rate = 100.0 if recent_patients > 0 else 0.0
            
            # Appointment completion rate
            total_appointments = self.env['hospital.appointment'].search_count([
                ('date_appointment', '>=', rec.date_from),
                ('date_appointment', '<=', rec.date_to)
            ])
            completed_appointments = self.env['hospital.appointment'].search_count([
                ('date_appointment', '>=', rec.date_from),
                ('date_appointment', '<=', rec.date_to),
                ('state', '=', 'done')
            ])
            rec.appointment_completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
            
            # Average bill amount
            all_bills = self.env['hospital.bill'].search([
                ('date_bill', '>=', rec.date_from),
                ('date_bill', '<=', rec.date_to),
                ('state', '=', 'paid')
            ])
            rec.average_bill_amount = sum(all_bills.mapped('total_amount')) / len(all_bills) if all_bills else 0

    def get_appointment_chart_data(self):
        """Get data for appointment status pie chart"""
        self.ensure_one()
        appointments = self.env['hospital.appointment'].search([
            ('date_appointment', '>=', self.date_from),
            ('date_appointment', '<=', self.date_to)
        ])
        
        data = {}
        for state in ['draft', 'confirmed', 'done', 'cancel']:
            count = len(appointments.filtered(lambda a: a.state == state))
            data[state] = count
        
        return data

    def get_revenue_chart_data(self):
        """Get monthly revenue data for the last 6 months"""
        self.ensure_one()
        result = []
        today = fields.Date.today()
        
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30 * i)
            first_day = month_date.replace(day=1)
            
            # Calculate last day of month
            if month_date.month == 12:
                last_day = month_date.replace(day=31)
            else:
                last_day = (month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1))
            
            bills = self.env['hospital.bill'].search([
                ('date_bill', '>=', first_day),
                ('date_bill', '<=', last_day),
                ('state', '=', 'paid')
            ])
            
            revenue = sum(bills.mapped('total_amount'))
            result.append({
                'month': month_date.strftime('%B %Y'),
                'revenue': revenue
            })
        
        return result

    def get_department_patient_distribution(self):
        """Get patient distribution by department"""
        self.ensure_one()
        departments = self.env['hospital.department'].search([('active', '=', True)])
        result = []
        
        for dept in departments:
            # Count appointments in this department through doctors
            doctors = self.env['hospital.doctor'].search([('department_id', '=', dept.id)])
            appointment_count = self.env['hospital.appointment'].search_count([
                ('doctor_id', 'in', doctors.ids),
                ('date_appointment', '>=', self.date_from),
                ('date_appointment', '<=', self.date_to)
            ])
            
            result.append({
                'department': dept.name,
                'count': appointment_count
            })
        
        return result

    def action_refresh_dashboard(self):
        """Refresh dashboard data"""
        self._compute_statistics()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
