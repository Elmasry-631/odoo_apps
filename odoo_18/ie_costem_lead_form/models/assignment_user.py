from odoo import fields, models


class AssignmentUser(models.Model):
    _inherit = "crm.lead"

    assignment_username = fields.Many2many('res.users', string='Assignment' )
