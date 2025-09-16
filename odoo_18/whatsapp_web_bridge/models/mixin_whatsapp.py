import re
import urllib.parse
from odoo import api, fields, models, _

class WhatsappMixin(models.AbstractModel):
    _name = 'whatsapp.mixin'
    _description = 'WhatsApp Mixin'

    def _wa_get_partner(self):
        self.ensure_one()
        partner = getattr(self, 'partner_id', False) or getattr(self, 'commercial_partner_id', False)
        if not partner and hasattr(self, 'message_partner_ids') and self.message_partner_ids:
            partner = self.message_partner_ids[0]
        return partner

    def _wa_normalize_phone(self, phone):
        if not phone:
            return False
        phone = re.sub(r'\D', '', phone)  # keep digits
        if phone.startswith('00'):
            phone = phone[2:]
        icp = self.env['ir.config_parameter'].sudo()
        cc = icp.get_param('whatsapp.default_country_code', '+966').lstrip('+')
        if phone.startswith('0'):
            phone = cc + phone[1:]
        # ensure has country code
        if not phone.startswith(cc):
            # assume already has country code if length > 10
            pass
        return '+' + phone if not phone.startswith('+') else phone

    def _wa_build_message(self, template_fallback):
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        model = self._name
        partner = self._wa_get_partner()
        vals = {
            'partner_name': partner.name if partner else '',
            'doc_name': getattr(self, 'name', ''),
            'amount_total': getattr(self, 'amount_total', 0.0),
            'task_name': getattr(self, 'name', ''),
        }
        # pick template by model
        if model == 'account.move':
            template = icp.get_param('whatsapp.template.invoice', template_fallback)
        elif model == 'sale.order':
            template = icp.get_param('whatsapp.template.sale', template_fallback)
        elif model == 'stock.picking':
            template = icp.get_param('whatsapp.template.picking', template_fallback)
        elif model == 'project.task':
            template = icp.get_param('whatsapp.template.task', template_fallback)
        elif model == 'res.partner':
            template = icp.get_param('whatsapp.template.contact', template_fallback)
        else:
            template = template_fallback
        try:
            return template.format_map(vals)
        except Exception:
            return template_fallback

    def _wa_open_url(self, phone, message):
        icp = self.env['ir.config_parameter'].sudo()
        use_wa_me = str(icp.get_param('whatsapp.use_wa_me', False)) in ('True','true','1')
        text = urllib.parse.quote(message or '')
        phone_digits = re.sub(r'\D', '', phone or '')
        if use_wa_me:
            url = f"https://wa.me/{phone_digits}?text={text}"
        else:
            url = f"https://web.whatsapp.com/send?phone={phone_digits}&text={text}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_send_whatsapp(self):
        self.ensure_one()
        partner = self._wa_get_partner()
        phone = False
        if partner:
            phone = partner.mobile or partner.phone or partner._fields.get('x_whatsapp') and getattr(partner, 'x_whatsapp')
        phone = self._wa_normalize_phone(phone)
        message = self._wa_build_message(_("Hello {partner_name}, regarding {doc_name}."))
        if not phone:
            self.env['whatsapp.log'].create({
                'res_model': self._name,
                'res_id': self.id,
                'partner_id': partner.id if partner else False,
                'phone': False,
                'message': message,
                'state': 'no_phone'
            })
            raise ValueError(_("No phone number found for the related partner."))
        self.env['whatsapp.log'].create({
            'res_model': self._name,
            'res_id': self.id,
            'partner_id': partner.id if partner else False,
            'phone': phone,
            'message': message,
            'state': 'ok'
        })
        return self._wa_open_url(phone, message)