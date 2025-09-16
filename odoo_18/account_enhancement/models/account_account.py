from odoo import api, fields, models

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_free_account = fields.Boolean("Free Account")
