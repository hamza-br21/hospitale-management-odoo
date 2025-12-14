from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HospitalAnalytics(models.TransientModel):
    _name = 'hospital.analytics'
    _description = 'Hospital Analytics and Reports'

    date_from = fields.Date(string='From Date', required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.today)
    report_type = fields.Selection([
        ('financial', 'Financial Report'),
        ('operational', 'Operational Report'),
        ('patient', 'Patient Analytics'),
        ('doctor', 'Doctor Performance'),
    ], string='Report Type', default='financial')

    def generate_financial_report(self):
        """Generate comprehensive financial report"""
        self.ensure_one()
        
        bills = self.env['hospital.bill'].search([
            ('date_bill', '>=', self.date_from),
            ('date_bill', '<=', self.date_to)
        ])
        
        total_revenue = sum(bills.filtered(lambda b: b.state == 'paid').mapped('total_amount'))
        pending_revenue = sum(bills.filtered(lambda b: b.state == 'draft').mapped('total_amount'))
        insurance_claims = sum(bills.mapped('insurance_coverage'))
        patient_payments = sum(bills.mapped('patient_payable'))
        
        # Revenue by payment method
        revenue_by_method = {}
        for method in ['cash', 'card', 'insurance', 'bank_transfer']:
            method_bills = bills.filtered(lambda b: b.payment_method == method and b.state == 'paid')
            revenue_by_method[method] = sum(method_bills.mapped('total_amount'))
        
        # Revenue by service type
        revenue_by_service = {}
        for bill in bills.filtered(lambda b: b.state == 'paid'):
            for line in bill.bill_line_ids:
                service_type = line.product_type
                if service_type not in revenue_by_service:
                    revenue_by_service[service_type] = 0
                revenue_by_service[service_type] += line.subtotal
        
        return {
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'insurance_claims': insurance_claims,
            'patient_payments': patient_payments,
            'revenue_by_method': revenue_by_method,
            'revenue_by_service': revenue_by_service,
            'total_bills': len(bills),
            'paid_bills': len(bills.filtered(lambda b: b.state == 'paid')),
            'pending_bills': len(bills.filtered(lambda b: b.state == 'draft')),
        }

    def generate_operational_report(self):
        """Generate operational metrics report"""
        self.ensure_one()
        
        # Appointment metrics
        appointments = self.env['hospital.appointment'].search([
            ('date_appointment', '>=', self.date_from),
            ('date_appointment', '<=', self.date_to)
        ])
        
        appointment_stats = {
            'total': len(appointments),
            'confirmed': len(appointments.filtered(lambda a: a.state == 'confirmed')),
            'done': len(appointments.filtered(lambda a: a.state == 'done')),
            'cancelled': len(appointments.filtered(lambda a: a.state == 'cancel')),
        }
        
        # Admission metrics
        admissions = self.env['hospital.admission'].search([
            ('admission_date', '>=', self.date_from),
            ('admission_date', '<=', self.date_to)
        ])
        
        total_stay_days = 0
        for admission in admissions.filtered(lambda a: a.discharge_date):
            stay = (admission.discharge_date - admission.admission_date).days
            total_stay_days += stay
        
        avg_stay = total_stay_days / len(admissions) if admissions else 0
        
        # Bed utilization
        total_beds = self.env['hospital.bed'].search_count([('active', '=', True)])
        occupied_beds = self.env['hospital.bed'].search_count([('state', '=', 'occupied')])
        
        # Prescription metrics
        prescriptions = self.env['hospital.prescription'].search([
            ('prescription_date', '>=', self.date_from),
            ('prescription_date', '<=', self.date_to)
        ])
        
        return {
            'appointments': appointment_stats,
            'admissions': {
                'total': len(admissions),
                'active': len(admissions.filtered(lambda a: a.state == 'admitted')),
                'discharged': len(admissions.filtered(lambda a: a.state == 'discharged')),
                'average_stay_days': round(avg_stay, 2),
            },
            'beds': {
                'total': total_beds,
                'occupied': occupied_beds,
                'available': total_beds - occupied_beds,
                'occupancy_rate': round((occupied_beds / total_beds * 100) if total_beds > 0 else 0, 2),
            },
            'prescriptions': {
                'total': len(prescriptions),
            }
        }

    def generate_patient_analytics(self):
        """Generate patient analytics report"""
        self.ensure_one()
        
        # New patients in period
        new_patients = self.env['hospital.patient'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to)
        ])
        
        # Patient demographics
        total_patients = self.env['hospital.patient'].search_count([('active', '=', True)])
        
        gender_distribution = {
            'male': self.env['hospital.patient'].search_count([('gender', '=', 'male'), ('active', '=', True)]),
            'female': self.env['hospital.patient'].search_count([('gender', '=', 'female'), ('active', '=', True)]),
            'other': self.env['hospital.patient'].search_count([('gender', '=', 'other'), ('active', '=', True)]),
        }
        
        # Age distribution
        patients = self.env['hospital.patient'].search([('active', '=', True)])
        age_groups = {
            '0-18': 0,
            '19-35': 0,
            '36-55': 0,
            '56-75': 0,
            '75+': 0,
        }
        
        for patient in patients:
            age = patient.age
            if age <= 18:
                age_groups['0-18'] += 1
            elif age <= 35:
                age_groups['19-35'] += 1
            elif age <= 55:
                age_groups['36-55'] += 1
            elif age <= 75:
                age_groups['56-75'] += 1
            else:
                age_groups['75+'] += 1
        
        # Blood group distribution
        blood_groups = {}
        for group in ['a+', 'a-', 'b+', 'b-', 'ab+', 'ab-', 'o+', 'o-']:
            count = self.env['hospital.patient'].search_count([
                ('blood_group', '=', group),
                ('active', '=', True)
            ])
            blood_groups[group.upper()] = count
        
        # Most frequent patients (by appointment count)
        appointments = self.env['hospital.appointment'].search([
            ('date_appointment', '>=', self.date_from),
            ('date_appointment', '<=', self.date_to)
        ])
        
        patient_visit_count = {}
        for apt in appointments:
            patient_id = apt.patient_id.id
            if patient_id not in patient_visit_count:
                patient_visit_count[patient_id] = {
                    'name': apt.patient_id.name,
                    'count': 0
                }
            patient_visit_count[patient_id]['count'] += 1
        
        # Sort by visit count
        top_patients = sorted(patient_visit_count.values(), key=lambda x: x['count'], reverse=True)[:10]
        
        return {
            'total_patients': total_patients,
            'new_patients': len(new_patients),
            'gender_distribution': gender_distribution,
            'age_distribution': age_groups,
            'blood_group_distribution': blood_groups,
            'top_frequent_patients': top_patients,
        }

    def generate_doctor_performance(self):
        """Generate doctor performance report"""
        self.ensure_one()
        
        doctors = self.env['hospital.doctor'].search([('active', '=', True)])
        doctor_stats = []
        
        for doctor in doctors:
            # Appointments handled
            appointments = self.env['hospital.appointment'].search([
                ('doctor_id', '=', doctor.id),
                ('date_appointment', '>=', self.date_from),
                ('date_appointment', '<=', self.date_to)
            ])
            
            # Prescriptions written
            prescriptions = self.env['hospital.prescription'].search([
                ('doctor_id', '=', doctor.id),
                ('prescription_date', '>=', self.date_from),
                ('prescription_date', '<=', self.date_to)
            ])
            
            # Revenue generated
            bills = self.env['hospital.bill'].search([
                ('appointment_id.doctor_id', '=', doctor.id),
                ('date_bill', '>=', self.date_from),
                ('date_bill', '<=', self.date_to),
                ('state', '=', 'paid')
            ])
            
            total_revenue = sum(bills.mapped('total_amount'))
            
            # Completion rate
            completed = len(appointments.filtered(lambda a: a.state == 'done'))
            completion_rate = (completed / len(appointments) * 100) if appointments else 0
            
            doctor_stats.append({
                'name': doctor.name,
                'specialization': doctor.specialization or 'General',
                'department': doctor.department_id.name if doctor.department_id else 'N/A',
                'appointments': len(appointments),
                'completed_appointments': completed,
                'completion_rate': round(completion_rate, 2),
                'prescriptions': len(prescriptions),
                'revenue_generated': total_revenue,
            })
        
        # Sort by appointments handled
        doctor_stats.sort(key=lambda x: x['appointments'], reverse=True)
        
        return {
            'doctor_performance': doctor_stats,
            'total_doctors': len(doctors),
            'most_busy_doctor': doctor_stats[0] if doctor_stats else None,
        }

    def action_generate_report(self):
        """Generate selected report"""
        self.ensure_one()
        
        if self.report_type == 'financial':
            data = self.generate_financial_report()
        elif self.report_type == 'operational':
            data = self.generate_operational_report()
        elif self.report_type == 'patient':
            data = self.generate_patient_analytics()
        elif self.report_type == 'doctor':
            data = self.generate_doctor_performance()
        else:
            data = {}
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.report_type.title()} Report',
            'res_model': 'hospital.analytics',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'report_data': data}
        }
