from odoo import models, fields


class CSTPoq(models.Model):
    _name = 'ie.cst.poq'

    product = fields.Many2one('product.product', string='Product')
    poq = fields.Many2many('product.product' , string='POQ')
