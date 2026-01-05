from odoo import api, fields, models

class HospitalDosage(models.Model):
    _name = "hospital.dosage"
    _description = "Prescription Dosage"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string='Dosage', required=True)
    abbreviation = fields.Char(string='Abbreviation')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The dosage name must be unique!')
    ]

class HospitalFrequency(models.Model):
    _name = "hospital.frequency"
    _description = "Prescription Frequency"
    _rec_name = "name"
    _order = "sequence, name"

    name = fields.Char(string='Frequency', required=True)
    code = fields.Char(string='Code', help="Short code e.g. BID, TID")
    sequence = fields.Integer(string="Sequence", default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The frequency name must be unique!')
    ]
