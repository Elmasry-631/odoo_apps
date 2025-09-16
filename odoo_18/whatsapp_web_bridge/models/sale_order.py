from odoo import models

class SaleOrder(models.Model):
    _inherit = ['sale.order', 'whatsapp.mixin']
    _name = 'sale.order'