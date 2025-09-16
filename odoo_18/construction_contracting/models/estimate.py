from odoo import api, fields, models


class ConstructionEstimate(models.Model):
    _name = "construction.estimate"
    _description = "Construction Estimate"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="اسم المقايسة", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="العميل", required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda s: s.env.company.currency_id)
    boq_ids = fields.Many2one("ie.cst.poq", string='BOQ')
    equipment_ids = fields.Many2one("product.template", string="Equipment")



    state = fields.Selection([
        ("draft", "مسودّة"),
        ("sent", "مرسلة"),
        ("confirmed", "مؤكَّدة")
    ], default="draft", required=True)

    version_count = fields.Integer(string="عدد الإصدارات", compute="_compute_version_count")
    quotation_count = fields.Integer(string="عدد الكوتيشن", compute="_compute_quotation_count")

    # علاقة One2many على الكوتيشنز
    quotation_ids = fields.One2many("sale.order", "x_estimate_id", string="الكوتيشنز")

    def action_send(self):
        self.write({"state": "sent"})

    def action_confirm(self):
        """تأكيد المقايسة → إنشاء كوتيشن جديد"""
        SaleOrder = self.env["sale.order"]
        for rec in self:
            order = SaleOrder.create({
                "partner_id": rec.partner_id.id,
                "company_id": rec.company_id.id,
                "currency_id": rec.currency_id.id,
                "origin": rec.name,
                "x_estimate_id": rec.id,  # ربط المقايسة بالكوتيشن
            })
            rec.state = "confirmed"

    def _compute_version_count(self):
        self.version_count = 0

    def _compute_quotation_count(self):
        for rec in self:
            rec.quotation_count = len(rec.quotation_ids)

    def action_view_quotations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")

        action.update({
            "domain": [("x_estimate_id", "=", self.id)],
            "context": {
                "default_x_estimate_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        })
        return action


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_estimate_id = fields.Many2one("construction.estimate", string="المقايسة")


# المراحل

# البند-< المكونات المعدات الانشطة عدد الافراد
