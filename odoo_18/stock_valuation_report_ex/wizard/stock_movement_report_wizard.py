# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime as py_datetime, timedelta, time


class StockMovementReportWizard(models.TransientModel):
    _name = 'stock.movement.report.wizard'
    _description = 'Stock Movement Report Wizard'

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_id = fields.Many2one('product.category', string="Product Category")

    def _build_report_products(self):
        products = self.product_ids
        if self.category_id:
            products |= self.env['product.product'].search([
                ('categ_id', 'child_of', self.category_id.id)
            ])
        return products.sorted(key=lambda p: p.name)

    def action_print_report(self):
        self.ensure_one()
        if not self.product_ids and not self.category_id:
            raise UserError(_("الرجاء اختيار منتج أو تصنيف على الأقل."))

        products = self._build_report_products()
        return self.env.ref(
            'stock_valuation_report_ex.action_report_stock_movement'
        ).report_action(
            self,  # هنا نخليها على الـ wizard مش products
            data={
                'date_from': self.date_from,
                'date_to': self.date_to,
                'product_ids': products.ids,
                'category_id': self.category_id.id if self.category_id else False,
            }
        )


class StockMovementReport(models.AbstractModel):
    _name = 'report.stock_valuation_report_ex.stock_movement_report_template'
    _description = 'Stock Movement and Valuation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env['stock.movement.report.wizard'].browse(docids)

        product_ids = data.get('product_ids') or wizard.mapped('product_ids').ids
        category_id = data.get('category_id') or (wizard.category_id.id if wizard.category_id else False)
        date_from = data.get('date_from') or wizard.date_from
        date_to = data.get('date_to') or wizard.date_to

        if not product_ids and not category_id:
            raise UserError(_("You must select at least one product or a product category."))

        # Products
        domain = [('id', 'in', product_ids)] if product_ids else [('categ_id', 'child_of', category_id)]
        products = self.env['product.product'].search(domain)
        if not products:
            raise UserError(_("No products found for the selected criteria."))

        category_name = self.env['product.category'].browse(category_id).name if category_id else _("All Products")
        products_map = {p.id: p for p in products}

        # Opening balance
        day_before_from = date_from - timedelta(days=1)
        opening_domain = [
            ('product_id', 'in', products.ids),
            ('date', '<=', py_datetime.combine(day_before_from, time.max))
        ]
        opening_data = self.env['stock.valuation.layer'].read_group(
            opening_domain, ['quantity', 'value'], ['product_id']
        )
        opening_balances = {p.id: {'qty': 0.0, 'value': 0.0} for p in products}
        for group in opening_data:
            pid = group['product_id'][0]
            opening_balances[pid]['qty'] = group['quantity']
            opening_balances[pid]['value'] = group['value']

        # Movements
        moves_domain = [
            ('product_id', 'in', products.ids),
            ('date', '>=', py_datetime.combine(date_from, time.min)),
            ('date', '<=', py_datetime.combine(date_to, time.max))
        ]
        layers = self.env['stock.valuation.layer'].search_read(
            moves_domain,
            fields=['date', 'product_id', 'quantity', 'value', 'unit_cost', 'stock_move_id'],
            order='date asc'
        )
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

        for product in products:
            opening = opening_balances[product.id]
            bal_price = opening['value'] / opening['qty'] if opening['qty'] else 0.0
            product_lines[product.id].append({
                'date': date_from,
                'movement_type': _('Opening Balance'),
                'reference': '',
                'in_qty': 0.0,
                'out_qty': 0.0,
                'bal_qty': opening['qty'],
                'bal_uom': product.uom_id.name,
                'bal_price': bal_price,
                'bal_total': opening['value'],
                'currency': product.currency_id or self.env.company.currency_id,
            })

        for layer in layers:
            pid = layer['product_id'][0]
            product = products_map[pid]
            move_info = moves_map.get(layer.get('stock_move_id', [False])[0], {})

            running_balances[pid]['qty'] += layer['quantity']
            running_balances[pid]['value'] += layer['value']
            bal_price = running_balances[pid]['value'] / running_balances[pid]['qty'] if running_balances[pid]['qty'] else 0.0

            is_in = layer['quantity'] > 0
            product_lines[pid].append({
                'date': layer['date'],
                'movement_type': move_info.get('picking_type', _('Inventory Adjustment')),
                'reference': move_info.get('ref', ''),
                'in_qty': layer['quantity'] if is_in else 0.0,
                'out_qty': -layer['quantity'] if not is_in else 0.0,
                'bal_qty': running_balances[pid]['qty'],
                'bal_uom': product.uom_id.name,
                'bal_price': bal_price,
                'bal_total': running_balances[pid]['value'],
                'currency': product.currency_id or self.env.company.currency_id,
            })

        for product in products:
            closing = running_balances[product.id]
            bal_price = closing['value'] / closing['qty'] if closing['qty'] else 0.0
            product_lines[product.id].append({
                'date': date_to,
                'movement_type': _('Closing Balance'),
                'reference': '',
                'in_qty': 0.0,
                'out_qty': 0.0,
                'bal_qty': closing['qty'],
                'bal_uom': product.uom_id.name,
                'bal_price': bal_price,
                'bal_total': closing['value'],
                'currency': product.currency_id or self.env.company.currency_id,
            })

        records = [{
            'product': product,
            'lines': product_lines[product.id],
        } for product in products]

        return {
            'doc_ids': docids,
            'doc_model': 'stock.movement.report.wizard',
            'data': {
                'category_name': category_name,
                'date_from': date_from,
                'date_to': date_to,
            },
            'docs': wizard,
            'records': records,
        }
