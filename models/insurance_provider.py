from odoo import api, fields, models, _

class HospitalInsuranceProvider(models.Model):
    _name = "hospital.insurance.provider"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Insurance Provider"
    _rec_name = "name"

    name = fields.Char(string='Name', required=True, tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    notes = fields.Text(string='Notes')
