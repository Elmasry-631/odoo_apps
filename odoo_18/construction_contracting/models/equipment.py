from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_equipment = fields.Boolean(string="Is Equipment", default=False)
