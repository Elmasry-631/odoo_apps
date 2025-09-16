
from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    debit_currency = fields.Monetary(
        string="Debit (Currency)",
        currency_field="currency_id",
        compute="_compute_currency_split",
        store=False
    )
    credit_currency = fields.Monetary(
        string="Credit (Currency)",
        currency_field="currency_id",
        compute="_compute_currency_split",
        store=False
    )

    def _compute_currency_split(self):
        for line in self:
            if line.amount_currency > 0:
                line.debit_currency = line.amount_currency
                line.credit_currency = 0.0
            elif line.amount_currency < 0:
                line.debit_currency = 0.0
                line.credit_currency = -line.amount_currency
            else:
                line.debit_currency = 0.0
                line.credit_currency = 0.0
