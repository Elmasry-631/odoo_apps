from odoo import models, fields

class RecruitmentContract(models.Model):
    _name = 'hr.recruitment.contract'
    _description = 'Recruitment Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Contract Reference", required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hr.recruitment.contract'))
    client_id = fields.Many2one('hr.recruitment.client', string="Client", required=True, tracking=True)
    job_order_id = fields.Many2one('hr.recruitment.job.order', string="Job Order", required=True, tracking=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, copy=False)

    payment_terms = fields.Selection([
        ('advance', 'Advance Payment'),
        ('monthly', 'Monthly Payment'),
        ('end', 'End of Contract Payment')
    ], string="Payment Terms", default='monthly', tracking=True)
    amount = fields.Float(string="Contract Amount")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)


    notes = fields.Text(string="Notes")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string="Status", default='draft', tracking=True)

    def action_activate(self):
        self.state = 'active'

    def action_expire(self):
        self.state = 'expired'


    def action_create_invoice(self):
        for rec in self:
            if not rec.client_id or not rec.client_id.partner_id:
                raise UserError("Please set a client with a linked Partner before creating an invoice.")
            if not rec.amount or rec.amount <= 0:
                raise UserError("Please set a valid Contract Amount.")

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.client_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Contract: {rec.name} - {rec.job_order_id.position or ""}',
                    'quantity': 1,
                    'price_unit': rec.amount,
                })]
            }
            invoice = self.env['account.move'].create(invoice_vals)
            rec.invoice_id = invoice.id

            return {
                'name': 'Invoice',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
            }