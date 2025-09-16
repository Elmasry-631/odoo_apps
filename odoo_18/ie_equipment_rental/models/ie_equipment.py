from odoo import models, fields

class Equipment(models.Model):
    _name = "equipment.equipment"
    _description = "Equipment"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product',string="Equipment Name", required=True)
    code = fields.Char(string="Code")
    category = fields.Selection([
        ('heavy', 'Heavy Equipment'),
        ('light', 'Light Equipment'),
        ('vehicle', 'Vehicle'),
    ], string="Category")
    cost = fields.Float(string="Cost")
    is_available = fields.Boolean(string="Available", default=True)

    property_account_income_id = fields.Many2one(
        'account.account',
        string='Income Account',
        domain=[('deprecated', '=', False)],
        help='Account used for rental income of this equipment.'
    )


