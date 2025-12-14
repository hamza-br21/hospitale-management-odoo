from odoo import api, fields, models, _

class HospitalPrescription(models.Model):
    _name = "hospital.prescription"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Medical Prescription"
    _rec_name = "reference"
    _order = "prescription_date desc"

    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    doctor_id = fields.Many2one('hospital.doctor', string="Doctor", required=True, tracking=True)
    prescription_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True, tracking=True)
    note = fields.Text(string='Note')
    prescription_line_ids = fields.One2many('hospital.prescription.line', 'prescription_id', string="Medicines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.prescription') or _('New')
        return super(HospitalPrescription, self).create(vals)

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

class HospitalPrescriptionLine(models.Model):
    _name = "hospital.prescription.line"
    _description = "Prescription Line"

    prescription_id = fields.Many2one('hospital.prescription', string="Prescription", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", domain="[('active', '=', True)]")
    name = fields.Char(string="Medicine", required=True)
    user_id = fields.Many2one('res.users', string="Prescribed By", default=lambda self: self.env.user)
    dosage = fields.Char(string="Dosage", help="e.g. 500mg")
    frequency = fields.Char(string="Frequency", help="e.g. 2 times a day")
    duration_days = fields.Integer(string="Duration (Days)", default=7)
    quantity = fields.Integer(string="Quantity", default=1)
    note = fields.Char(string="Instruction")

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        if self.medicine_id:
            self.name = self.medicine_id.name
