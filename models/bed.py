from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalBed(models.Model):
    _name = "hospital.bed"
    _description = "Hospital Bed"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Bed Name', required=True, tracking=True)
    room_id = fields.Many2one('hospital.room', string='Room', tracking=True)
    bed_type = fields.Selection([
        ('standard', 'Standard'),
        ('icu', 'ICU'),
        ('vip', 'VIP'),
    ], string='Bed Type', default='standard', required=True, tracking=True)
    state = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ], string='Status', default='free', tracking=True)
    current_patient_id = fields.Many2one('hospital.patient', string='Current Patient', compute='_compute_current_patient', store=True)
    admission_ids = fields.One2many('hospital.admission', 'bed_id', string='Admissions')
    
    _sql_constraints = [
        ('unique_bed_name', 'unique(name)', 'The bed name must be unique!')
    ]

    @api.depends('admission_ids.state')
    def _compute_current_patient(self):
        for rec in self:
            active_admission = rec.admission_ids.filtered(lambda a: a.state == 'active')
            rec.current_patient_id = active_admission[0].patient_id if active_admission else False
