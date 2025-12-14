from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patient File"

    name = fields.Char(string='Name', required=True, tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True, tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], required=True, default='male', tracking=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string='Blood Group')
    active = fields.Boolean(string="Active", default=True)
    
    # Relational fields
    appointment_ids = fields.One2many('hospital.appointment', 'patient_id', string='Appointments')
    admission_ids = fields.One2many('hospital.admission', 'patient_id', string='Admissions')
    prescription_ids = fields.One2many('hospital.prescription', 'patient_id', string='Prescriptions')
    bill_ids = fields.One2many('hospital.bill', 'patient_id', string='Bills')
    insurance_ids = fields.One2many('hospital.insurance', 'patient_id', string='Insurance Policies')
    
    # Computed fields for smart buttons
    appointment_count = fields.Integer(string='Appointments', compute='_compute_appointment_count')
    admission_count = fields.Integer(string='Admissions', compute='_compute_admission_count')
    bill_count = fields.Integer(string='Bills', compute='_compute_bill_count')
    
    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                today = fields.Date.today()
                rec.age = relativedelta(today, rec.date_of_birth).years
            else:
                rec.age = 0

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    @api.depends('admission_ids')
    def _compute_admission_count(self):
        for rec in self:
            rec.admission_count = len(rec.admission_ids)

    @api.depends('bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth > fields.Date.today():
                raise ValidationError(_("The Date of Birth cannot be in the future!"))

    def action_view_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'domain': [('patient_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_patient_id': self.id}
        }

    def action_view_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bills',
            'res_model': 'hospital.bill',
            'domain': [('patient_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_patient_id': self.id}
        }
