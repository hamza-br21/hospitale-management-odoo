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

    def action_send_email(self):
        """ Opens a wizard to compose an email, with pre-loaded template """
        self.ensure_one()
        template_id = self.env.ref('gestion_hospitaliere.prescription_email_template_new').id
        ctx = {
            'default_model': 'hospital.prescription',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

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
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", domain="[('active', '=', True)]", required=True)
    name = fields.Char(string="Medicine", required=True)
    user_id = fields.Many2one('res.users', string="Prescribed By", default=lambda self: self.env.user)
    dosage_id = fields.Many2one('hospital.dosage', string="Dosage")
    frequency_id = fields.Many2one('hospital.frequency', string="Frequency")
    duration_days = fields.Integer(string="Duration (Days)", default=7)
    quantity = fields.Integer(string="Quantity", default=1)
    note = fields.Char(string="Instruction")

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        if self.medicine_id:
            self.name = self.medicine_id.name
