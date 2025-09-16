# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# =========================
# 1) رأس المستخلص (IPC Head)
# =========================
class ConstructionIPC(models.Model):
    _name = "construction.ipc"
    _description = "Construction Progress Certificate (IPC)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(string="المرجع", required=True, copy=False, default=lambda s: _("New"))
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    project_id = fields.Many2one("project.project", string="المشروع", required=True, index=True)
    partner_id = fields.Many2one("res.partner", string="العميل", related="project_id.partner_id", store=True, readonly=True)

    period_start = fields.Date(string="فترة من", required=True, default=lambda s: fields.Date.context_today(s))
    period_end = fields.Date(string="فترة إلى", required=True, default=lambda s: fields.Date.context_today(s))
    state = fields.Selection([
        ("draft", "مسودة"),
        ("approved", "معتمد"),
        ("invoiced", "مفوّتَر"),
    ], string="الحالة", default="draft", tracking=True)

    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True, readonly=True)

    line_ids = fields.One2many("construction.ipc.line", "ipc_id", string="بنود المستخلص")
    daywork_line_ids = fields.One2many("construction.ipc.daywork.line", "ipc_id", string="Dayworks")

    amount_lines = fields.Monetary(string="إجمالي البنود", compute="_compute_amounts", store=True)
    amount_dayworks = fields.Monetary(string="إجمالي اليوميات", compute="_compute_amounts", store=True)
    gross_before_tax = fields.Monetary(string="الإجمالي قبل الضريبة", compute="_compute_amounts", store=True)

    # مبسّط: خصومات/إضافات (قبل الضريبة)
    retention_amount = fields.Monetary(string="Retention", default=0.0)
    advance_deduction = fields.Monetary(string="Advance Recovery", default=0.0)
    lds_amount = fields.Monetary(string="Liquidated Damages", default=0.0)
    net_before_tax = fields.Monetary(string="الصافي قبل الضريبة", compute="_compute_net", store=True)
    contract_id = fields.Many2one(
        "sale.order",
        string="العقد (Contract)",
        domain="[('state', '=', 'sale'), ('partner_id', '=', partner_id)]",
        ondelete="restrict",
        help="أمر البيع المؤكد الذي يمثل عقد العميل المرتبط بالمستخلص."
    )

    # قفل الإقفال الشهري (Cut-off)
    is_locked_by_cutoff = fields.Boolean(string="مقفول بعد الإقفال", default=False)

    @api.depends("line_ids.amount_this_period", "daywork_line_ids.amount")
    def _compute_amounts(self):
        for rec in self:
            lines_total = sum(rec.line_ids.mapped("amount_this_period"))
            dayworks_total = sum(rec.daywork_line_ids.mapped("amount"))
            rec.amount_lines = lines_total
            rec.amount_dayworks = dayworks_total
            rec.gross_before_tax = lines_total + dayworks_total

    @api.depends("gross_before_tax", "retention_amount", "advance_deduction", "lds_amount")
    def _compute_net(self):
        for rec in self:
            rec.net_before_tax = (rec.gross_before_tax or 0.0) - (rec.retention_amount or 0.0) - (rec.advance_deduction or 0.0) - (rec.lds_amount or 0.0)

    def action_approve(self):
        for rec in self:
            if rec.is_locked_by_cutoff:
                raise ValidationError(_("هذا المستخلص مقفول بسبب الإقفال الشهري."))
            rec.state = "approved"

    def action_make_invoice(self):
        """مستقبلاً: إنشاء فاتورة عميل من IPC المعتمد."""
        for rec in self:
            if rec.state != "approved":
                raise ValidationError(_("يجب اعتماد المستخلص أولاً."))
            # TODO: إنشاء فاتورة (account.move) وربطها
            rec.state = "invoiced"

    # منع تعديل مستند مقفول
    def write(self, vals):
        locked = any(self.filtered(lambda r: r.is_locked_by_cutoff and r.state == "draft"))
        if locked and any(k for k in vals.keys() if k not in ("message_follower_ids", "message_ids")):
            raise ValidationError(_("تم تجاوز الـCut-off الشهري، لا يمكن التعديل على هذا المستخلص."))
        return super().write(vals)

    # كرون: يقفل أي IPC مسودّة انتهت فترته قبل أول يوم في الشهر الحالي
    @api.model
    def _cron_lock_after_cutoff(self):
        first_of_month = date.today().replace(day=1)
        recs = self.sudo().search([("state", "=", "draft"), ("period_end", "<", first_of_month)])
        recs.write({"is_locked_by_cutoff": True})
        return True


# ==============================
# 2) بنود المستخلص (IPC Lines)
# ==============================
class ConstructionIPCLine(models.Model):
    _name = "construction.ipc.line"
    _description = "IPC Line"
    _check_company_auto = True

    ipc_id = fields.Many2one("construction.ipc", string="المستخلص", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="ipc_id.company_id", store=True, readonly=True)
    currency_id = fields.Many2one(related="ipc_id.currency_id", store=True, readonly=True)

    description = fields.Char("الوصف")
    uom_id = fields.Many2one("uom.uom", string="الوحدة", required=True)
    qty_this_period = fields.Float(string="كمية هذه الفترة", required=True, default=0.0)
    rate = fields.Monetary(string="سعر الوحدة", required=True)
    amount_this_period = fields.Monetary(string="قيمة هذه الفترة", compute="_compute_amount", store=True)

    qty_contract_total = fields.Float(string="الكمية التعاقدية", required=True, default=0.0)
    qty_to_date = fields.Float(string="كمية حتى تاريخه", compute="_compute_to_date", store=True)

    @api.depends("qty_this_period", "rate")
    def _compute_amount(self):
        for rec in self:
            qty = max(rec.qty_this_period or 0.0, 0.0)
            rec.amount_this_period = qty * (rec.rate or 0.0)

    @api.depends("qty_this_period")
    def _compute_to_date(self):
        # مبدئيًا: تراكمي بسيط (يمكن لاحقًا ربطه بتاريخ السجل/الفترات السابقة)
        for rec in self:
            rec.qty_to_date = max(rec.qty_this_period or 0.0, 0.0)

    @api.constrains("qty_to_date", "qty_contract_total")
    def _check_not_exceed_contract(self):
        for rec in self:
            if (rec.qty_to_date or 0.0) > (rec.qty_contract_total or 0.0) + 1e-6:
                raise ValidationError(_("تجاوزت الكمية التعاقدية."))


# ====================================
# 3) بنود Dayworks (Labour/Equip/Mat)
# ====================================
class IPCDayworkLine(models.Model):
    _name = "construction.ipc.daywork.line"
    _description = "Daywork Line"
    _check_company_auto = True

    ipc_id = fields.Many2one("construction.ipc", string="المستخلص", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="ipc_id.company_id", store=True, readonly=True)
    currency_id = fields.Many2one(related="ipc_id.currency_id", store=True, readonly=True)

    category = fields.Selection([
        ("labour", "عمالة"),
        ("equipment", "معدات"),
        ("materials", "مواد"),
    ], string="الفئة", required=True)

    resource_ref = fields.Char(string="المورد/المرجع")
    hours_or_days = fields.Float(string="عدد الساعات/الأيام", required=True, default=0.0)
    unit_rate = fields.Monetary(string="سعر الوحدة", required=True)
    amount = fields.Monetary(string="الإجمالي", compute="_compute_amount", store=True)

    @api.depends("hours_or_days", "unit_rate")
    def _compute_amount(self):
        for rec in self:
            qty = max(rec.hours_or_days or 0.0, 0.0)
            rec.amount = qty * (rec.unit_rate or 0.0)
