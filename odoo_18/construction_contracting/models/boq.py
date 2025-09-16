from odoo import fields, models, api

class POQ(models.Model):
    _name = "ie.cst.poq"
    _description = "POQ"

    f_product = fields.Many2one('product.product', string='Product')
    material_line_ids = fields.One2many('ie.cst.poq.line', 'poq_id', string='POQ Materials')

    @api.onchange('f_product')
    def _onchange_f_product(self):
        if self.f_product:
            # امسح القديم
            self.material_line_ids = [(5, 0, 0)]
            # هات الـ BoM بتاع المنتج
            bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.f_product.product_tmpl_id.id)], limit=1)
            if bom:
                lines = []
                for line in bom.bom_line_ids:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_qty,
                        'uom_id': line.product_uom_id.id,
                    }))
                self.material_line_ids = lines


class POQLine(models.Model):
    _name = "ie.cst.poq.line"
    _description = "POQ Line"

    poq_id = fields.Many2one('ie.cst.poq', string="POQ", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Material")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        'uom.category',
        string="UoM Category",
        related="product_id.uom_id.category_id",
        store=True,
        readonly=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # لما يختار المنتج، يجيب الـ UoM الافتراضي بتاعه
            self.uom_id = self.product_id.uom_id.id