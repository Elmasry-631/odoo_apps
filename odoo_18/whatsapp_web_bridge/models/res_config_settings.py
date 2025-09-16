from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_default_country_code = fields.Char(string="Default Country Code", default="+966", help="Used when numbers start with 0 or missing country code.")
    whatsapp_use_wa_me = fields.Boolean(string="Use wa.me instead of WhatsApp Web", default=False)
    whatsapp_template_invoice = fields.Text(string="Invoice Template", default="Hello {partner_name}, your invoice {doc_name} for {amount_total} is ready.")
    whatsapp_template_sale = fields.Text(string="Quotation/Order Template", default="Hello {partner_name}, your order {doc_name} total {amount_total}.")
    whatsapp_template_picking = fields.Text(string="Delivery Template", default="Hello {partner_name}, your delivery {doc_name} is scheduled.")
    whatsapp_template_task = fields.Text(string="Task Template", default="Hello {partner_name}, update for task {doc_name}: {task_name}.")
    whatsapp_template_contact = fields.Text(string="Contact Template", default="Hello {partner_name}, nice connecting with you.")

    def set_values(self):
        res = super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('whatsapp.default_country_code', self.whatsapp_default_country_code or '')
        params.set_param('whatsapp.use_wa_me', self.whatsapp_use_wa_me)
        params.set_param('whatsapp.template.invoice', self.whatsapp_template_invoice or '')
        params.set_param('whatsapp.template.sale', self.whatsapp_template_sale or '')
        params.set_param('whatsapp.template.picking', self.whatsapp_template_picking or '')
        params.set_param('whatsapp.template.task', self.whatsapp_template_task or '')
        params.set_param('whatsapp.template.contact', self.whatsapp_template_contact or '')
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            whatsapp_default_country_code=params.get_param('whatsapp.default_country_code', '+966'),
            whatsapp_use_wa_me=params.get_param('whatsapp.use_wa_me', default=False),
            whatsapp_template_invoice=params.get_param('whatsapp.template.invoice', ''),
            whatsapp_template_sale=params.get_param('whatsapp.template.sale', ''),
            whatsapp_template_picking=params.get_param('whatsapp.template.picking', ''),
            whatsapp_template_task=params.get_param('whatsapp.template.task', ''),
            whatsapp_template_contact=params.get_param('whatsapp.template.contact', ''),
        )
        return res