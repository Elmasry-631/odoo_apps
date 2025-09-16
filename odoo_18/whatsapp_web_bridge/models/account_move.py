from odoo import models

class AccountMove(models.Model):
    _inherit = ['account.move', 'whatsapp.mixin']
    _name = 'account.move'