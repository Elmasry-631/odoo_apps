# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ConstructionProductionLog(models.Model):
    _name = "construction.production.log"
    _description = "Daily Production Log"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]

    date = fields.Date(string="التاريخ", required=True, default=fields.Date.context_today)
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    project_id = fields.Many2one("project.project", string="المشروع", required=True)
    task_id = fields.Many2one("project.task", string="النشاط/المهمة", domain="[('project_id','=',project_id)]")
    boq_ref = fields.Char("مرجع BOQ (اختياري)")
    qty_done = fields.Float(string="الكمية المنفّذة", default=0.0)
    manhours = fields.Float(string="ساعات عمالة", default=0.0)
    equipment_hours = fields.Float(string="ساعات معدات", default=0.0)
    productivity = fields.Float(string="الإنتاجية", compute="_compute_prod", store=True,
                                help="Qty/Manhours إن توفّرت، وإلا صفر.")

    @api.depends("qty_done", "manhours")
    def _compute_prod(self):
        for rec in self:
            rec.productivity = rec.qty_done / rec.manhours if rec.manhours > 0 else 0.0

    @api.constrains("qty_done", "manhours", "equipment_hours")
    def _check_positive(self):
        for rec in self:
            if any(v < 0 for v in (rec.qty_done, rec.manhours, rec.equipment_hours)):
                raise ValidationError(_("القيم لا يجوز أن تكون سالبة."))

    # (اختياري) ربط IPC لاحقًا بتجميع الكميات للفترة
