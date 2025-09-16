from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    custom_account_field_id = fields.Many2one(
        'account.account', string='Custom Account Field',
        help='Custom account field for valuation adjustments.'
    )
    journal_items_count = fields.Integer(
        string='Journal Items Count',
        compute='_compute_journal_items_count'
    )
    def _compute_journal_items_count(self):
        for picking in self:
            # نجيب الـ account.move.line عن طريق stock.valuation.layer
            valuation_layers = self.env['stock.valuation.layer'].search([
                ('stock_move_id', 'in', picking.move_ids.ids)
            ])
            moves = valuation_layers.mapped('account_move_id')
            count = self.env['account.move.line'].search_count([
                ('move_id', 'in', moves.ids)
            ])
            picking.journal_items_count = count

    def action_view_journal_items(self):
        self.ensure_one()
        valuation_layers = self.env['stock.valuation.layer'].search([
            ('stock_move_id', 'in', self.move_ids.ids)
        ])
        moves = valuation_layers.mapped('account_move_id')
        lines = self.env['account.move.line'].search([('move_id', 'in', moves.ids)])
        action = self.env.ref('account.action_account_moves_all').read()[0]
        action['domain'] = [('id', 'in', lines.ids)]
        return action



class StockMove(models.Model):
    _inherit = "stock.move"

    custom_account_field_id = fields.Many2one(
        'account.account', string='Account',
        help='Custom account field for valuation adjustments.'
    )

    def _get_accounting_data_for_valuation(self):
        """
        Override to inject custom account if defined.
        Returns: (journal_id, acc_src, acc_dest, acc_valuation)
        """
        journal_id, acc_src, acc_dest, acc_valuation = super()._get_accounting_data_for_valuation()

        for move in self:
            if move.custom_account_field_id:
                acc_dest = move.custom_account_field_id.id
        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id=False, description=False
    ):
        """
        Override to force unique account.move.line per stock move line
        even if account is the same.
        """
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )

        # 🔥 Force unique name per line so Odoo won't merge
        for line in res:
            line[2]['name'] = f"{line[2].get('name', '')}"

        return res


    def _get_merge_candidates(self):
        """مفيش أي مرشحين للدمج في Stock Move"""
        return self.browse()

    def _merge_moves(self, merge_into=False, merge=True):
        """تعطيل دمج الـ Stock Move"""
        return self

    def _prepare_merge_moves_distinct_fields(self):
        """تفريغ الحقول اللي أودو بيعتمد عليها في الدمج"""
        return []

    def _account_entry_move(self, qty, description, svl_id, cost):
        """
        Override to pass mtno_field and picking name to Account Move ref
        """
        moves_vals = super()._account_entry_move(qty, description, svl_id, cost)
        for vals in moves_vals:
            picking_name = self.picking_id.name if self.picking_id else ''
            mtno = self.mtno_field or ''
            if picking_name or mtno:
                vals['ref'] = f"({picking_name}) - {mtno}" if picking_name and mtno else picking_name or mtno
        return moves_vals



class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @staticmethod
    def _get_merge_move_line_fields():
        """تعطيل دمج detailed operations"""
        return []



