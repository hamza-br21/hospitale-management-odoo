from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalAdmission(models.Model):
    _name = "hospital.admission"
    _description = "Patient Admission"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "reference"
    _order = "date_admission desc"

    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    doctor_id = fields.Many2one('hospital.doctor', string="Doctor", tracking=True)
    date_admission = fields.Datetime(string='Admission Date', default=fields.Datetime.now, required=True, tracking=True)
    discharge_date = fields.Datetime(string='Discharge Date', tracking=True)
    bed_id = fields.Many2one('hospital.bed', string="Bed", domain="[('state', '=', 'free')]", tracking=True)
    admission_type = fields.Selection([
        ('emergency', 'Emergency'),
        ('planned', 'Planned'),
        ('observation', 'Observation'),
    ], string='Admission Type', default='planned', tracking=True)
    diagnosis = fields.Text(string="Diagnosis")
    discharge_summary = fields.Text(string="Discharge Summary")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('discharged', 'Discharged'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.admission') or _('New')
        return super(HospitalAdmission, self).create(vals)

    def action_admit(self):
        for rec in self:
            if not rec.bed_id:
                raise ValidationError(_("Please select a bed for admission!"))
            if rec.bed_id.state != 'free':
                raise ValidationError(_("The selected bed is not free!"))
            rec.bed_id.state = 'occupied'
            rec.state = 'active'
    
    def action_discharge(self):
        for rec in self:
            rec.discharge_date = fields.Datetime.now()
            if rec.bed_id:
                rec.bed_id.state = 'free'
            rec.state = 'discharged'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'active' and rec.bed_id:
                rec.bed_id.state = 'free'
            rec.state = 'cancel'
