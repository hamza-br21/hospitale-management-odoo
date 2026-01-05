from odoo import api, fields, models, _

class HospitalSpecialization(models.Model):
    _name = "hospital.specialization"
    _description = "Doctor Specialization"
    _rec_name = "name"

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The specialization name must be unique !')
    ]
