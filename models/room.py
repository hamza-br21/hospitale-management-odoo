# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class HospitalRoom(models.Model):
    _name = "hospital.room"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hospital Room/Ward"
    _rec_name = "name"

    name = fields.Char(string='Room Number', required=True, tracking=True)
    room_type = fields.Selection([
        ('general', 'General Ward'),
        ('private', 'Private Room'),
        ('semi_private', 'Semi-Private Room'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency'),
        ('operation', 'Operation Theater'),
    ], string='Room Type', default='general', required=True, tracking=True)
    department_id = fields.Many2one('hospital.department', string="Department", tracking=True)
    bed_ids = fields.One2many('hospital.bed', 'room_id', string="Beds")
    capacity = fields.Integer(string='Capacity', compute='_compute_capacity', store=True)
    occupied_beds = fields.Integer(string='Occupied Beds', compute='_compute_occupied_beds')
    available_beds = fields.Integer(string='Available Beds', compute='_compute_available_beds')
    floor = fields.Char(string='Floor')
    daily_rate = fields.Float(string='Daily Rate', help='Daily room charge')
    description = fields.Text(string='Description')
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        ('unique_room_name', 'unique(name)', 'Room number must be unique!')
    ]

    @api.depends('bed_ids')
    def _compute_capacity(self):
        for rec in self:
            rec.capacity = len(rec.bed_ids)

    @api.depends('bed_ids.state')
    def _compute_occupied_beds(self):
        for rec in self:
            rec.occupied_beds = len(rec.bed_ids.filtered(lambda b: b.state == 'occupied'))

    @api.depends('capacity', 'occupied_beds')
    def _compute_available_beds(self):
        for rec in self:
            rec.available_beds = rec.capacity - rec.occupied_beds
