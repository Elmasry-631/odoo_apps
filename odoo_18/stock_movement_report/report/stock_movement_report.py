# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from datetime import datetime as py_datetime, timedelta

class StockMovementReport(models.AbstractModel):
    _name = 'report.stock_movement_report.stock_movement_report_template'
    _description = 'Stock Movement and Valuation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        docs = self.env['stock.movement.report.wizard'].browse(docids)

        product_ids = data.get('product_ids') or docs.mapped('product_ids').ids
        category_id = data.get('category_id') or (docs.category_id.id if docs.category_id else False)
        date_from = data.get('date_from') or docs.date_from
        date_to = data.get('date_to') or docs.date_to

        if not product_ids and not category_id:
            raise UserError(_("You must select at least one product or a product category."))

        # Products domain
        product_domain = []
        if product_ids:
            product_domain.append(('id', 'in', product_ids))
        elif category_id:
            product_domain.append(('categ_id', 'child_of', category_id))

        products = self.env['product.product'].search(product_domain)
        if not products:
            raise UserError(_("No products found for the selected criteria."))

        category_name = self.env['product.category'].browse(category_id).name if category_id else _("All Products")
        products_map = {p.id: p for p in products}

        # Opening balance
        day_before_from = date_from - timedelta(days=1)
        opening_domain = [
            ('product_id', 'in', products.ids),
            ('date', '<=', py_datetime.combine(day_before_from, py_datetime.max.time()))
        ]
        opening_data = self.env['stock.valuation.layer'].read_group(
            opening_domain, ['quantity', 'value'], ['product_id']
        )
        opening_balances = {p.id: {'qty': 0.0, 'value': 0.0} for p in products}
        for group in opening_data:
            prod_id = group['product_id'][0]
            opening_balances[prod_id]['qty'] = group['quantity']
            opening_balances[prod_id]['value'] = group['value']

        # Movements in range
        moves_domain = [
            ('product_id', 'in', products.ids),
            ('date', '>=', py_datetime.combine(date_from, py_datetime.min.time())),
            ('date', '<=', py_datetime.combine(date_to, py_datetime.max.time()))
        ]
        layers = self.env['stock.valuation.layer'].search_read(
            moves_domain,
            fields=['date', 'product_id', 'quantity', 'value', 'unit_cost', 'stock_move_id'],
            order='date asc'
        )

        # Prefetch moves
        move_ids = [l['stock_move_id'][0] for l in layers if l.get('stock_move_id')]
        moves_map = {
            m.id: {
                'ref': m.reference,
                'picking_type': m.picking_type_id.display_name,
                'partner': m.picking_id.partner_id.name,
            } for m in self.env['stock.move'].browse(move_ids)
        }

        # Process lines
        product_lines = {p.id: [] for p in products}
        running_balances = {pid: bal.copy() for pid, bal in opening_balances.items()}

        for layer in layers:
            prod_id = layer['product_id'][0]
            product = products_map[prod_id]
            move_info = moves_map.get(layer.get('stock_move_id', [False])[0], {})

            running_balances[prod_id]['qty'] += layer['quantity']
            running_balances[prod_id]['value'] += layer['value']

            bal_price = running_balances[prod_id]['value'] / running_balances[prod_id]['qty'] \
                        if running_balances[prod_id]['qty'] else 0.0
            is_in = layer['quantity'] > 0

            line = {
                'date': layer['date'],
                'movement_type': move_info.get('picking_type', _('Inventory Adjustment')),
                'reference': move_info.get('ref', ''),

                'in_qty': layer['quantity'] if is_in else 0.0,
                'in_uom': product.uom_id.name if is_in else '',
                'in_price': layer['unit_cost'] if is_in else 0.0,
                'in_total': layer['value'] if is_in else 0.0,

                'out_qty': -layer['quantity'] if not is_in else 0.0,
                'out_uom': product.uom_id.name if not is_in else '',
                'out_price': layer['unit_cost'] if not is_in else 0.0,
                'out_total': -layer['value'] if not is_in else 0.0,

                'bal_qty': running_balances[prod_id]['qty'],
                'bal_uom': product.uom_id.name,
                'bal_price': bal_price,
                'bal_total': running_balances[prod_id]['value'],
                'currency': product.currency_id or self.env.company.currency_id,
            }
            product_lines[prod_id].append(line)

        # Final records
        records = []
        for product in products:
            if opening_balances[product.id]['qty'] or product_lines[product.id]:
                records.append({
                    'product': product,
                    'lines': product_lines[product.id],
                })

        return {
            'doc_ids': docids,
            'doc_model': 'stock.movement.report.wizard',
            'data': {
                'category_name': category_name,
                'date_from': date_from,
                'date_to': date_to,
            },
            'docs': docs,
            'records': records,
        }
