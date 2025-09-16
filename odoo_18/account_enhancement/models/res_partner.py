# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PartnerCode(models.Model):
    _name = 'partner.code'
    # res_partner_id = fields.Many2one('res.partner')
    name = fields.Char('Code')

    _sql_constraints = [
        ('code_uniq', 'unique (name)', "Tag code already exists!"),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    code_id = fields.Many2one('partner.code')

