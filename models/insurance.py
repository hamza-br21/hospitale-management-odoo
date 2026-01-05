# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalInsurance(models.Model):
    _name = "hospital.insurance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patient Insurance"
    _rec_name = "policy_number"

    policy_number = fields.Char(string='Policy Number', required=True, tracking=True)
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    provider_id = fields.Many2one('hospital.insurance.provider', string='Insurance Provider', required=True, tracking=True)
    coverage_percentage = fields.Float(string='Coverage %', default=80.0, tracking=True, help='Percentage of costs covered by insurance')
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    is_active = fields.Boolean(string='Active', compute='_compute_is_active', store=True)
    max_coverage_amount = fields.Float(string='Max Coverage Amount', help='Maximum amount covered by policy')
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_policy_number', 'unique(policy_number)', 'Policy number must be unique!')
    ]

    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            if rec.start_date and rec.start_date <= today:
                if not rec.end_date or rec.end_date >= today:
                    rec.is_active = True
                else:
                    rec.is_active = False
            else:
                rec.is_active = False

    @api.constrains('coverage_percentage')
    def _check_coverage_percentage(self):
        for rec in self:
            if rec.coverage_percentage < 0 or rec.coverage_percentage > 100:
                raise ValidationError(_("Coverage percentage must be between 0 and 100!"))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_("End date cannot be before start date!"))
