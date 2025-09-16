from odoo import models, fields


class Weekday(models.Model):
    _name = 'weekday'
    _description = 'Weekday'

    name = fields.Char(string='Name', required=True)
