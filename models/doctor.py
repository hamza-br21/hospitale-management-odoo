from odoo import api, fields, models, _

class HospitalDoctor(models.Model):
    _name = "hospital.doctor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Doctor Record"
    _rec_name = "name"

    name = fields.Char(string='Name', required=True, tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', default='male', tracking=True)
    specialization = fields.Char(string='Specialization', tracking=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    department_id = fields.Many2one('hospital.department', string="Department", tracking=True)
    image = fields.Binary(string="Doctor Image")
    signature = fields.Binary(string="Signature")
    active = fields.Boolean(string="Active", default=True)
    
    # Relational fields
    appointment_ids = fields.One2many('hospital.appointment', 'doctor_id', string='Appointments')
    prescription_ids = fields.One2many('hospital.prescription', 'doctor_id', string='Prescriptions')
    
    # Computed fields
    appointment_count = fields.Integer(string='Appointments', compute='_compute_appointment_count')

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    def action_view_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'domain': [('doctor_id', '=', self.id)],
            'view_mode': 'tree,form,calendar',
            'context': {'default_doctor_id': self.id}
        }
