# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ConstructionContract(models.Model):
    _name = "construction.contract"
    _description = "Construction Contract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(string="اسم العقد", required=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    project_id = fields.Many2one("project.project", string="المشروع", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="العميل/الاستشاري", required=True)
    currency_id = fields.Many2one("res.currency", string="العملة", required=True, default=lambda s: s.env.company.currency_id)

    # سياسات العقد (قبل الضريبة)
    retention_rate = fields.Float(string="Retention %", default=lambda s: float(s.env["ir.config_parameter"].sudo().get_param("construction.default_retention_rate", 10.0)))
    advance_percent = fields.Float(string="Advance %", default=lambda s: float(s.env["ir.config_parameter"].sudo().get_param("construction.default_advance_percent", 20.0)))
    advance_recovery_ipcs = fields.Integer(string="عدد المستخلصات لاسترداد المقدّم", default=lambda s: int(s.env["ir.config_parameter"].sudo().get_param("construction.default_advance_recovery_ipcs", 10)))
    ld_rate_per_day = fields.Float(string="LDs نسبة/يوم", default=lambda s: float(s.env["ir.config_parameter"].sudo().get_param("construction.default_ld_rate_per_day", 0.0)))
    ld_cap_percent = fields.Float(string="LDs سقف %", default=lambda s: float(s.env["ir.config_parameter"].sudo().get_param("construction.default_ld_cap_percent", 10.0)))

    state = fields.Selection([
        ("draft", "مسودّة"),
        ("active", "مفعّل"),
        ("closed", "مغلق"),
    ], default="draft", tracking=True, required=True)

    def action_activate_contract(self):
        for rec in self:
            # تحقق توافُق الشركة، وتوفر Analytic على المشروع
            if not rec.project_id.analytic_account_id:
                raise ValidationError(_("يجب تحديد الحساب التحليلي (Analytic) على المشروع."))
            rec.state = "active"

    def action_close_contract(self):
        self.write({"state": "closed"})

    @api.constrains("retention_rate", "advance_percent", "ld_cap_percent")
    def _check_percentages(self):
        for rec in self:
            for val in (rec.retention_rate, rec.advance_percent, rec.ld_cap_percent):
                if val < 0.0 or val > 100.0:
                    raise ValidationError(_("النِّسب يجب أن تكون بين 0% و 100%."))
