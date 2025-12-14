from odoo import api, fields, models, _

class HospitalBill(models.Model):
    _name = "hospital.bill"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hospital Bill"
    _rec_name = "reference"
    _order = "date_bill desc"

    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    admission_id = fields.Many2one('hospital.admission', string="Related Admission", tracking=True)
    appointment_id = fields.Many2one('hospital.appointment', string="Related Appointment", tracking=True)
    date_bill = fields.Date(string='Date', default=fields.Date.today, required=True, tracking=True)
    due_date = fields.Date(string='Due Date', tracking=True)
    bill_line_ids = fields.One2many('hospital.bill.line', 'bill_id', string='Bill Lines')
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts', store=True)
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_amounts', store=True, tracking=True)
    amount = fields.Float(string="Amount", compute='_compute_amounts', store=True, tracking=True)  # Keep for compatibility
    insurance_id = fields.Many2one('hospital.insurance', string='Insurance Policy', domain="[('patient_id', '=', patient_id), ('is_active', '=', True)]")
    insurance_coverage = fields.Float(string='Insurance Coverage', compute='_compute_insurance_coverage', store=True)
    patient_payable = fields.Float(string='Patient Payable', compute='_compute_insurance_coverage', store=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
    ], string='Payment Method', tracking=True)
    note = fields.Text(string='Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.bill') or _('New')
        return super(HospitalBill, self).create(vals)

    def action_paid(self):
        for rec in self:
            rec.state = 'paid'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.depends('bill_line_ids.subtotal')
    def _compute_amounts(self):
        for rec in self:
            subtotal = sum(rec.bill_line_ids.mapped('subtotal'))
            rec.subtotal = subtotal
            rec.tax_amount = subtotal * 0.0  # No tax for now, can be customized
            rec.total_amount = subtotal + rec.tax_amount
            rec.amount = rec.total_amount

    @api.depends('total_amount', 'insurance_id', 'insurance_id.coverage_percentage')
    def _compute_insurance_coverage(self):
        for rec in self:
            if rec.insurance_id and rec.insurance_id.is_active:
                coverage = (rec.total_amount * rec.insurance_id.coverage_percentage) / 100
                rec.insurance_coverage = min(coverage, rec.insurance_id.max_coverage_amount or coverage)
                rec.patient_payable = rec.total_amount - rec.insurance_coverage
            else:
                rec.insurance_coverage = 0.0
                rec.patient_payable = rec.total_amount


class HospitalBillLine(models.Model):
    _name = "hospital.bill.line"
    _description = "Hospital Bill Line"

    bill_id = fields.Many2one('hospital.bill', string='Bill', required=True, ondelete='cascade')
    product_type = fields.Selection([
        ('consultation', 'Consultation Fee'),
        ('room', 'Room Charges'),
        ('medicine', 'Medicine'),
        ('procedure', 'Procedure'),
        ('lab', 'Laboratory Test'),
        ('other', 'Other'),
    ], string='Type', required=True, default='other')
    medicine_id = fields.Many2one('hospital.medicine', string='Medicine', domain="[('active', '=', True)]")
    description = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        if self.medicine_id:
            self.description = self.medicine_id.name
            self.unit_price = self.medicine_id.unit_price
            self.product_type = 'medicine'
