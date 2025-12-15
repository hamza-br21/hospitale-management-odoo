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
    ], string='Status', default='draft', required=True, tracking=True, group_expand='_expand_states')

    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

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

    def write(self, vals):
        # 1. Handle state change to 'discharged' or 'cancel' (Free the bed)
        if vals.get('state') in ['discharged', 'cancel']:
             for rec in self:
                 if rec.bed_id and rec.bed_id.state == 'occupied':
                     rec.bed_id.state = 'free'
                 if vals.get('state') == 'discharged' and not rec.discharge_date:
                     rec.discharge_date = fields.Datetime.now()

        # 2. Handle state change to 'active' (re-admission) or initial activation
        if vals.get('state') == 'active':
            for rec in self:
                # Only check if we are NOT already active (to allow idempotent updates/demo data)
                if rec.state != 'active':
                    # If bed_id is in vals, we will handle it in the second block.
                    # If bed_id is NOT in vals, we must validate the current rec.bed_id
                    if not vals.get('bed_id') and rec.bed_id:
                        if rec.bed_id.state != 'free':
                            raise ValidationError(_("The bed %s is already occupied by another patient!") % rec.bed_id.name)
                        rec.bed_id.state = 'occupied'
                    rec.discharge_date = False
        
        # 3. Handle bed change while active
        if vals.get('bed_id'):
            for rec in self:
                new_bed_id = vals.get('bed_id')
                # Only proceed if the bed is actually changing
                if rec.bed_id.id != new_bed_id:
                    if rec.state == 'active' and rec.bed_id:
                         rec.bed_id.state = 'free' # Free old bed
                    
                    new_bed = self.env['hospital.bed'].browse(new_bed_id)
                    # Use 'active' from vals if available (switching to active), or current state
                    new_state = vals.get('state') or rec.state
                    
                    if new_state == 'active' and new_bed.state != 'free':
                         raise ValidationError(_("The bed %s is not free!") % new_bed.name)
                    
                    if new_state == 'active':
                        new_bed.state = 'occupied'

        return super(HospitalAdmission, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.bed_id and rec.bed_id.state == 'occupied':
                rec.bed_id.state = 'free'
        return super(HospitalAdmission, self).unlink()
