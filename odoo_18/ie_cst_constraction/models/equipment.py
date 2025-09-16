from odoo import fields, models


class CSTEquipment(models.Model):
    _name = "ie.cst.equipment"

    equipment = fields.Many2one('product.product', string="Equipment")
    description = fields.Text()
