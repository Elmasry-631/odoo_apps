from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class RecruitmentDeployment(models.Model):
    _name = 'hr.recruitment.deployment'
    _description = 'Worker Deployment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    worker_id = fields.Many2one('hr.recruitment.worker', string="Worker", required=True, tracking=True)
    client_id = fields.Many2one('hr.recruitment.client', string="Client", required=True, tracking=True)
    job_order_id = fields.Many2one('hr.recruitment.job.order', string="Job Order", tracking=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True, readonly=1)
    salary = fields.Float(string="Salary Offer", tracking=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, copy=False)

    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('leave', 'On Leave'),
        ('completed', 'Completed')
    ], string="Status", default='draft', tracking=True)

    notes = fields.Text(string="Notes")

    @api.onchange('job_order_id')
    def _onchange_job_order_id(self):
        if self.job_order_id:
            self.client_id = self.job_order_id.client_id
            self.salary = self.job_order_id.salary
            if self.start_date and self.job_order_id.contract_duration:
                self.end_date = self.start_date + relativedelta(months=self.job_order_id.contract_duration)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.job_order_id and self.job_order_id.contract_duration:
            self.end_date = self.start_date + relativedelta(months=self.job_order_id.contract_duration)

    def action_set_draft(self):
        self.status = 'draft'

    def action_set_active(self):
        self.status = 'active'

    def action_set_leave(self):
        self.status = 'leave'

    def action_set_completed(self):
        self.status = 'completed'

    def action_create_invoice(self):
        self.ensure_one()

        if not self.client_id:
            raise UserError(_("No client assigned."))
        if not self.job_order_id or not self.job_order_id.salary:
            raise UserError(_("No salary/amount set in Job Order."))
        if self.invoice_id:
            raise UserError(_("Invoice already created."))

        partner = self.client_id.partner_id
        if not partner:
            raise UserError(_("Client has no linked partner."))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f"Job Order: {self.job_order_id.name} | From {self.start_date} to {self.end_date}",
                'quantity': 1,
                'price_unit': self.job_order_id.salary,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
        }
