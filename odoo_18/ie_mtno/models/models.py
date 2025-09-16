from odoo import fields, models, api


class AddFieldMTNO(models.Model):
    _inherit = "stock.move"

    mtno_field = fields.Char(string="MTNO")
    unit_price = fields.Float(string="Unit Price", compute="_compute_unit_price", store=True)
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)

    @api.depends('unit_price', 'product_uom_qty')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.unit_price * rec.product_uom_qty

    @api.depends('product_id', 'product_id.standard_price')
    def _compute_unit_price(self):
        for rec in self:
            rec.unit_price = rec.product_id.standard_price if rec.product_id else 0.0
