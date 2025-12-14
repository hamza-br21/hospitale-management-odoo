# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalMedicine(models.Model):
    _name = "hospital.medicine"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Medicine Catalog"
    _rec_name = "name"

    name = fields.Char(string='Medicine Name', required=True, tracking=True)
    generic_name = fields.Char(string='Generic Name', tracking=True)
    category = fields.Selection([
        ('antibiotic', 'Antibiotic'),
        ('painkiller', 'Painkiller'),
        ('vitamin', 'Vitamin'),
        ('antiseptic', 'Antiseptic'),
        ('antiviral', 'Antiviral'),
        ('other', 'Other'),
    ], string='Category', default='other', required=True, tracking=True)
    manufacturer = fields.Char(string='Manufacturer')
    unit_price = fields.Float(string='Unit Price', tracking=True)
    stock_quantity = fields.Integer(string='Stock Quantity', default=0, tracking=True)
    description = fields.Text(string='Description')
    dosage_form = fields.Selection([
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
    ], string='Dosage Form', default='tablet')
    strength = fields.Char(string='Strength', help='e.g. 500mg, 10ml')
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        ('unique_medicine_name', 'unique(name, strength)', 'Medicine with this name and strength already exists!')
    ]

    @api.constrains('unit_price')
    def _check_unit_price(self):
        for rec in self:
            if rec.unit_price < 0:
                raise ValidationError(_("Unit price cannot be negative!"))

    @api.constrains('stock_quantity')
    def _check_stock_quantity(self):
        for rec in self:
            if rec.stock_quantity < 0:
                raise ValidationError(_("Stock quantity cannot be negative!"))

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        for rec in self:
            if rec.expiry_date and rec.expiry_date < fields.Date.today():
                raise ValidationError(_("Cannot add expired medicine! Expiry date must be in the future."))
