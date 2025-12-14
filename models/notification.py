from odoo import api, fields, models, _
import requests
import json
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HospitalNotification(models.Model):
    _name = 'hospital.notification'
    _description = 'Hospital Notification System'
    _order = 'create_date desc'

    name = fields.Char(string='Subject', required=True)
    message = fields.Text(string='Message', required=True)
    notification_type = fields.Selection([
        ('appointment_reminder', 'Appointment Reminder'),
        ('bill_due', 'Bill Due Reminder'),
        ('prescription_refill', 'Prescription Refill'),
        ('admission_alert', 'Admission Alert'),
        ('general', 'General Notification'),
    ], string='Type', default='general', required=True)
    recipient_type = fields.Selection([
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('all', 'All Users'),
    ], string='Recipient Type', required=True, default='patient')
    patient_id = fields.Many2one('hospital.patient', string='Patient')
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    send_via_email = fields.Boolean(string='Send via Email', default=True)
    send_via_sms = fields.Boolean(string='Send via SMS', default=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string='Status', default='draft')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    sent_date = fields.Datetime(string='Sent Date', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)

    def action_send_notification(self):
        """Send notification via configured channels"""
        for rec in self:
            try:
                if rec.send_via_email:
                    rec._send_email_notification()
                
                if rec.send_via_sms:
                    rec._send_sms_notification()
                
                rec.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now()
                })
            except Exception as e:
                rec.write({
                    'state': 'failed',
                    'error_message': str(e)
                })
                _logger.error(f"Failed to send notification: {str(e)}")

    def _send_email_notification(self):
        """Send email notification"""
        self.ensure_one()
        
        recipient_email = None
        if self.patient_id:
            recipient_email = self.patient_id.email
        elif self.doctor_id:
            recipient_email = self.doctor_id.email
        
        if not recipient_email:
            raise ValueError("No email address found for recipient")
        
        mail_values = {
            'subject': self.name,
            'body_html': self.message,
            'email_to': recipient_email,
        }
        
        self.env['mail.mail'].create(mail_values).send()

    def _send_sms_notification(self):
        """Send SMS notification via external API"""
        self.ensure_one()
        
        phone = None
        if self.patient_id:
            phone = self.patient_id.phone
        elif self.doctor_id:
            phone = self.doctor_id.phone
        
        if not phone:
            raise ValueError("No phone number found for recipient")
        
        # This is a placeholder for SMS API integration
        # Replace with your actual SMS provider (Twilio, Nexmo, etc.)
        _logger.info(f"SMS would be sent to {phone}: {self.message}")

    @api.model
    def send_appointment_reminders(self):
        """Cron job to send appointment reminders"""
        tomorrow = fields.Date.today() + timedelta(days=1)
        appointments = self.env['hospital.appointment'].search([
            ('date_appointment', '>=', tomorrow),
            ('date_appointment', '<', tomorrow + timedelta(days=1)),
            ('state', '=', 'confirmed')
        ])
        
        for appointment in appointments:
            notification = self.create({
                'name': f'Appointment Reminder - {appointment.reference}',
                'message': f"""
                    Dear {appointment.patient_id.name},
                    
                    This is a reminder for your appointment tomorrow:
                    
                    Doctor: {appointment.doctor_id.name}
                    Date & Time: {appointment.date_appointment}
                    Type: {appointment.appointment_type.title()}
                    
                    Please arrive 15 minutes early.
                    
                    Best regards,
                    Hospital Management Team
                """,
                'notification_type': 'appointment_reminder',
                'recipient_type': 'patient',
                'patient_id': appointment.patient_id.id,
                'send_via_email': True,
            })
            notification.action_send_notification()

    @api.model
    def send_bill_reminders(self):
        """Cron job to send bill payment reminders"""
        today = fields.Date.today()
        overdue_bills = self.env['hospital.bill'].search([
            ('state', '=', 'draft'),
            ('due_date', '<=', today)
        ])
        
        for bill in overdue_bills:
            notification = self.create({
                'name': f'Bill Payment Reminder - {bill.reference}',
                'message': f"""
                    Dear {bill.patient_id.name},
                    
                    This is a reminder that your bill is due:
                    
                    Bill Reference: {bill.reference}
                    Amount Due: ${bill.patient_payable:.2f}
                    Due Date: {bill.due_date}
                    
                    Please make payment at your earliest convenience.
                    
                    Best regards,
                    Hospital Billing Department
                """,
                'notification_type': 'bill_due',
                'recipient_type': 'patient',
                'patient_id': bill.patient_id.id,
                'send_via_email': True,
            })
            notification.action_send_notification()


class HospitalExternalAPI(models.TransientModel):
    _name = 'hospital.external.api'
    _description = 'External API Integration'

    def get_weather_info(self, city='Paris'):
        """Get weather information for hospital location"""
        try:
            # Using OpenWeatherMap API (requires API key)
            # This is a demo - you need to sign up at openweathermap.org
            api_key = self.env['ir.config_parameter'].sudo().get_param('hospital.weather_api_key', '')
            
            if not api_key:
                return {
                    'temperature': 'N/A',
                    'condition': 'API key not configured',
                    'humidity': 'N/A',
                }
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': f"{data['main']['temp']}°C",
                    'condition': data['weather'][0]['description'],
                    'humidity': f"{data['main']['humidity']}%",
                    'icon': data['weather'][0]['icon'],
                }
            else:
                return {
                    'temperature': 'N/A',
                    'condition': 'Unable to fetch weather',
                    'humidity': 'N/A',
                }
        except Exception as e:
            _logger.error(f"Weather API error: {str(e)}")
            return {
                'temperature': 'N/A',
                'condition': 'Error fetching data',
                'humidity': 'N/A',
            }

    def get_health_news(self):
        """Get latest health news (demo function)"""
        try:
            return [
                {
                    'title': 'New Medical Breakthrough Announced',
                    'description': 'Scientists discover new treatment method',
                    'date': fields.Date.today(),
                },
                {
                    'title': 'Healthcare Technology Advances',
                    'description': 'AI improving diagnosis accuracy',
                    'date': fields.Date.today(),
                },
            ]
        except Exception as e:
            _logger.error(f"News API error: {str(e)}")
            return []

    def validate_insurance(self, insurance_number):
        """Validate insurance via external API"""
        try:
            # Placeholder for insurance validation API
            # Replace with actual insurance provider API
            return {
                'valid': True,
                'provider': 'Sample Insurance Co.',
                'coverage': '80%',
                'status': 'Active'
            }
        except Exception as e:
            _logger.error(f"Insurance API error: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
