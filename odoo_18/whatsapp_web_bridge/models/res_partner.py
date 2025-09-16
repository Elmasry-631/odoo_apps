from odoo import models

class ResPartner(models.Model):
    _inherit = ['res.partner', 'whatsapp.mixin']
    _name = 'res.partner'