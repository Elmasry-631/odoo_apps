from odoo import fields, models

class WhatsappLog(models.Model):
    _name = 'whatsapp.log'
    _description = 'WhatsApp Send Log'
    _order = 'create_date desc'

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    phone = fields.Char(string='Phone')
    message = fields.Text(string='Message')
    state = fields.Selection([('ok','Opened'),('no_phone','No Phone')], default='ok')