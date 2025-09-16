from odoo import models, fields

class RecruitmentClient(models.Model):
    _name = 'hr.recruitment.client'
    _description = 'Recruitment Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        'res.partner',
        string="Contact",
        required=True,
        tracking=True
    )
    name = fields.Char(related='partner_id.name', store=True, readonly=True)

    client_type = fields.Selection([
        ('company', 'Company'),
        ('individual', 'Individual')
    ], string="Client Type", default='company', tracking=True)

    # قراءة الحقول مباشرة من الـ contact
    phone = fields.Char(related='partner_id.phone', store=True, readonly=False)
    email = fields.Char(related='partner_id.email', store=True, readonly=False)
    address = fields.Char(related='partner_id.contact_address', store=True, readonly=True)

    contract_ids = fields.One2many('hr.recruitment.contract', 'client_id', string="Contracts")
    job_order_ids = fields.One2many('hr.recruitment.job.order', 'client_id', string="Job Orders")
