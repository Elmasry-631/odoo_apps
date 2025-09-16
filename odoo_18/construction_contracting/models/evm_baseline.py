# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ConstructionBaselinePeriod(models.Model):
    _name = "construction.baseline.period"
    _description = "Baseline PV by Month (S-Curve)"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    project_id = fields.Many2one("project.project", string="المشروع", required=True, index=True)
    period = fields.Date(string="الشهر", required=True, help="أول يوم من الشهر (YYYY-MM-01).")
    pv_amount = fields.Monetary(string="Planned Value (PV)", required=True, default=0.0)
    currency_id = fields.Many2one(related="project_id.company_id.currency_id", store=True, readonly=True)

    _sql_constraints = [
        ("period_unique", "unique(project_id, period)", "موجود PV لهذا المشروع في هذا الشهر بالفعل."),
    ]

    @api.constrains("period")
    def _check_period_first_day(self):
        for rec in self:
            if rec.period and fields.Date.from_string(rec.period).day != 1:
                raise ValidationError(_("يجب أن يكون تاريخ الفترة اليوم الأول من الشهر."))
