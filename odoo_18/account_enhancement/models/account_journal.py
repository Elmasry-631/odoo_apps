from odoo import fields, models, api
class AccountJournal (models.Model):
    _inherit = 'account.journal'

    is_free_jornal =  fields.Boolean("Free Jornal")


