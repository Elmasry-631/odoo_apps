from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_free_journal = fields.Boolean(
        string="Free Journal",
        compute='_compute_is_free_journal',
        store=True
    )

    @api.depends('line_ids.account_id.is_free_journal')
    def _compute_is_free_journal(self):
        for move in self:
            move.is_free_journal = any(
                line.account_id.is_free_journal for line in move.line_ids
            )
