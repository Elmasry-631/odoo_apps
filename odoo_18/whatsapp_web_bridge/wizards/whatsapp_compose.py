from odoo import api, fields, models, _

class WhatsappCompose(models.TransientModel):
    _name = 'whatsapp.compose'
    _description = 'Compose WhatsApp Message'

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    phone = fields.Char(string='Phone')
    message = fields.Text(string='Message')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        record = self.env[active_model].browse(active_id)
        res.update({
            'res_model': active_model,
            'res_id': active_id,
            'partner_id': getattr(record, 'partner_id', False).id if hasattr(record, 'partner_id') else False,
            'message': record._wa_build_message(_("Hello {partner_name}, regarding {doc_name}.")),
            'phone': (getattr(record._wa_get_partner(), 'mobile', False) or getattr(record._wa_get_partner(), 'phone', False) or ''),
        })
        return res

    def action_send(self):
        self.ensure_one()
        record = self.env[self.res_model].browse(self.res_id)
        # override phone/message if edited
        partner = record._wa_get_partner()
        phone = self.phone or (partner.mobile or partner.phone)
        phone = record._wa_normalize_phone(phone)
        if not phone:
            raise ValueError(_("No phone number defined."))
        return record._wa_open_url(phone, self.message or '')