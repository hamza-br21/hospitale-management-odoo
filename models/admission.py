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
                if rec.state != 'active':
                    # Determine which bed we are validating (current or new)
                    target_bed_id = vals.get('bed_id') or rec.bed_id.id
                    if target_bed_id:
                        # Check for ACTUAL active admissions for this bed, excluding current record
                        existing_active = self.search([
                            ('bed_id', '=', target_bed_id),
                            ('state', '=', 'active'),
                            ('id', '!=', rec.id)
                        ], limit=1)
                        
                        if existing_active:
                             raise ValidationError(_("The bed is occupied by patient %s (Reference: %s)") % (existing_active.patient_id.name, existing_active.reference))
                        
                        # Mark bed as occupied (even if it was already 'occupied' by mistake/phantom)
                        self.env['hospital.bed'].browse(target_bed_id).write({'state': 'occupied'})
                        rec.discharge_date = False

        # 3. Handle bed change (independent of state change, or WITH state change)
        if vals.get('bed_id'):
            for rec in self:
                old_bed = rec.bed_id
                new_bed_id = vals.get('bed_id')
                
                if old_bed.id != new_bed_id:
                     # If we are active (or becoming active), the OLD bed must be freed
                     # But only if we are truly moving (not just setting same ID)
                     is_becoming_active = (vals.get('state') == 'active') or (rec.state == 'active' and vals.get('state') != 'discharged')
                     
                     if is_becoming_active and old_bed:
                         old_bed.write({'state': 'free'})
                     
                     if is_becoming_active:
                         # We already validated availability in Block 2 if state is changing to active.
                         # But if state IS ALREADY active and we just change bed, we must validate new bed here.
                         if not vals.get('state') == 'active': # If not handled by Block 2
                             existing_active = self.search([
                                ('bed_id', '=', new_bed_id),
                                ('state', '=', 'active'),
                                ('id', '!=', rec.id)
                             ], limit=1)
                             if existing_active:
                                 raise ValidationError(_("The bed is occupied by patient %s") % existing_active.patient_id.name)
                             self.env['hospital.bed'].browse(new_bed_id).write({'state': 'occupied'})

        return super(HospitalAdmission, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.bed_id and rec.bed_id.state == 'occupied':
                rec.bed_id.state = 'free'
        return super(HospitalAdmission, self).unlink()
