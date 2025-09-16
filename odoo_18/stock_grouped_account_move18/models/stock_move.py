# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.tools.float_utils import float_is_zero
from itertools import groupby
import logging

_logger = logging.getLogger(__name__)


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    def _validate_accounting_entries(self):
        """
        Override: نعمل قيد واحد لكل Picking بإجمالي التحويل.
        """
        if not self:
            return

        for picking, svls in groupby(sorted(self, key=lambda s: s.stock_move_id.picking_id.id),
                                     key=lambda s: s.stock_move_id.picking_id):
            svls = self.browse([s.id for s in svls])
            move = svls[0].stock_move_id
            company = move.company_id
            journal_id = move.product_id.categ_id.property_stock_journal.id
            ref_val = picking.name or _('Stock Picking')

            total_amount = 0.0
            debit_account_id = False
            credit_account_id = False

            for svl in svls:
                accounts = svl.product_id.product_tmpl_id.get_product_accounts()
                debit_account_id = accounts['stock_valuation'].id
                credit_account_id = accounts['stock_input'].id
                total_amount += svl.value

            if float_is_zero(total_amount, precision_rounding=company.currency_id.rounding):
                continue

            line_vals = [
                (0, 0, {
                    'name': ref_val,
                    'account_id': debit_account_id,
                    'debit': total_amount if total_amount > 0 else 0.0,
                    'credit': -total_amount if total_amount < 0 else 0.0,
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                }),
                (0, 0, {
                    'name': ref_val,
                    'account_id': credit_account_id,
                    'debit': -total_amount if total_amount < 0 else 0.0,
                    'credit': total_amount if total_amount > 0 else 0.0,
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                }),
            ]

            move_vals = {
                'move_type': 'entry',
                'journal_id': journal_id,
                'date': fields.Date.context_today(self),
                'ref': ref_val,
                'company_id': company.id,
                'line_ids': line_vals,
            }

            account_move = self.env['account.move'].create(move_vals)
            svls.write({'account_move_id': account_move.id})

            _logger.warning(">>> Created SINGLE journal entry for picking %s total=%s",
                            picking.name, total_amount)
