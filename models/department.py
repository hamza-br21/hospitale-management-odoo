from odoo import api, fields, models, _

class HospitalDepartment(models.Model):
    _name = "hospital.department"
    _description = "Department"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string="Active", default=True)
