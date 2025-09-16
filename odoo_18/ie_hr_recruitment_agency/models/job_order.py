from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecruitmentJobOrder(models.Model):
    _name = 'hr.recruitment.job.order'
    _description = 'Recruitment Job Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Order Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hr.recruitment.job.order')
    )
    client_id = fields.Many2one('hr.recruitment.client', string="Client", required=True, tracking=True)
    position = fields.Char(string="Position", required=True, tracking=True)
    quantity = fields.Integer(string="Number of Workers", default=1, tracking=True)
    skills_required = fields.Text(string="Required Skills")
    salary = fields.Float(string="Salary Offer")
    contract_duration = fields.Integer(string="Contract Duration (Months)")
    work_location = fields.Char(string="Work Location")

    state = fields.Selection([
        ('new', 'New'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
        ('closed', 'Closed')
    ], string="Status", default='new', tracking=True)

    worker_ids = fields.Many2many('hr.recruitment.worker', string="Assigned Workers")

    # تحقق عند الحفظ
    @api.constrains('worker_ids', 'quantity')
    def _check_workers_equal_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than 0."))
            assigned = len(rec.worker_ids)
            if assigned != rec.quantity:
                raise ValidationError(
                    _("You must assign exactly %s workers; currently %s.")
                    % (rec.quantity, assigned)
                )

    # تحقق عند تغيير الحالة
    def _ensure_workers_equal_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than 0."))
            assigned = len(rec.worker_ids)
            if assigned != rec.quantity:
                raise ValidationError(
                    _("You must assign exactly %s workers; currently %s.")
                    % (rec.quantity, assigned)
                )
    # ---------- أزرار الحالة مع التحقق ----------
    def action_set_processing(self):
        self._ensure_workers_equal_quantity()
        self.state = 'processing'

    def action_set_delivered(self):
        self._ensure_workers_equal_quantity()
        self.state = 'delivered'

    def action_set_closed(self):
        self._ensure_workers_equal_quantity()
        self.state = 'closed'

    def name_get(self):
        result = []
        for rec in self:
            client_name = rec.client_id.name if rec.client_id else "No Client"
            position = rec.position or "No Position"
            qty = rec.quantity or 0
            state_display = dict(self._fields['state'].selection).get(rec.state, rec.state)
            display_name = f"{client_name} - {position} ({qty} عامل) [{state_display}]"
            result.append((rec.id, display_name))
        return result
