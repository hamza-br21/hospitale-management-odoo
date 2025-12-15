from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Appointment"
    _rec_name = "reference"
    _order = "date_appointment desc"

    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    doctor_id = fields.Many2one('hospital.doctor', string="Doctor", required=True, tracking=True)
    date_appointment = fields.Datetime(string='Date', required=True, default=fields.Datetime.now, tracking=True)
    duration = fields.Float(string='Duration (hours)', default=0.5)
    appointment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('checkup', 'Check-up'),
    ], string='Type', default='consultation')
    note = fields.Text(string='Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    @api.constrains('doctor_id', 'date_appointment', 'duration')
    def check_doctor_availability(self):
        for rec in self:
            if not rec.doctor_id or not rec.date_appointment:
                continue
            
            # Calculate End Date
            from datetime import timedelta
            end_date = rec.date_appointment + timedelta(hours=rec.duration)
            
            # Search for overlapping appointments
            # Logic: (StartA < EndB) and (EndA > StartB)
            domain = [
                ('doctor_id', '=', rec.doctor_id.id),
                ('id', '!=', rec.id),
                ('state', '!=', 'cancel'),
                ('date_appointment', '<', end_date),
            ]
            
            overlapping_appointments = self.search(domain)
            
            for appointment in overlapping_appointments:
                appointment_end = appointment.date_appointment + timedelta(hours=appointment.duration)
                if appointment_end > rec.date_appointment:
                    raise ValidationError(_("Doctor %s is already booked at this time (Ref: %s).") % (rec.doctor_id.name, appointment.reference))

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or _('New')
        return super(HospitalAppointment, self).create(vals)

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def write(self, vals):
        # 1. Execute the write
        res = super(HospitalAppointment, self).write(vals)
        
        # 2. Check for state change to 'confirmed'
        if vals.get('state') == 'confirmed':
            for rec in self:
                rec._send_confirmation_email()
        return res

    def _send_confirmation_email(self):
        """ Separate method to handle email sending logic """
        self.ensure_one()
        # Send Email Notification
        if not self.patient_id.email:
             # Warning instead of silent fail
             raise ValidationError(_("Cannot send confirmation: Patient %s has no email address.") % self.patient_id.name)
        
        try:
            template = self.env.ref('gestion_hospitaliere.appointment_confirmation_email_template', raise_if_not_found=True)
            template.send_mail(self.id, force_send=True)
        except ValueError:
            raise ValidationError(_("Email Template 'appointment_confirmation_email_template' not found. Please update the module."))
        except Exception as e:
             raise ValidationError(_("Email sending failed: %s") % str(e))
