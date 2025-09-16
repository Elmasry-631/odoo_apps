# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime as py_datetime, timedelta


# =======================================================
#  Wizard Model: To get user input from the screen
# =======================================================
class StockMovementReportWizard(models.TransientModel):
    _name = 'stock.movement.report.wizard'
    _description = 'Stock Movement Report Wizard'

    date_from = fields.Date(string="From Date", required=True, default=fields.Date.today)
    date_to = fields.Date(string="To Date", required=True, default=fields.Date.today)
    product_ids = fields.Many2many('product.product', string="Products")
    category_id = fields.Many2one('product.category', string="Product Category")

    def _build_report_products(self):
        """Helper to get all products based on selection."""
        products = self.product_ids
        if self.category_id:
            # Using '|=' to add products without duplicates
            products |= self.env['product.product'].search([
                ('categ_id', 'child_of', self.category_id.id),
                ('type', '=', 'product')  # Ensure we only get stockable products
            ])
        return products

    def action_print_report(self):
        self.ensure_one()
        products = self._build_report_products()
        if not products:
            raise UserError(_("Please select at least one product or a category with products."))

        # Pass all the necessary data to the report action
        data = {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'product_ids': products.ids,
            'category_id': self.category_id.id if self.category_id else False,
        }
        return self.env.ref(
            'stock_valuation_report_ex.action_report_stock_movement'
        ).report_action(self, data=data)


# =======================================================
#  Report's Abstract Model: To prepare data for QWeb
# =======================================================
class StockMovementReport(models.AbstractModel):
    _name = 'report.stock_valuation_report_ex.stock_movement_report_template'
    _description = 'Stock Movement and Valuation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}

        # Correctly get and convert dates from string to date objects
        date_from_str = data.get('date_from')
        date_to_str = data.get('date_to')
        date_from = fields.Date.from_string(date_from_str)
        date_to = fields.Date.from_string(date_to_str)

        product_ids = data.get('product_ids', [])
        products = self.env['product.product'].browse(product_ids)
        if not products:
            raise UserError(_("No products found for the selected criteria."))

        category_id = data.get('category_id')
        category_name = self.env['product.category'].browse(category_id).name if category_id else _(
            "All Selected Products")

        # Calculate Opening balance
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
            opening_balances[prod_id]['qty'] = group.get('quantity', 0.0)
            opening_balances[prod_id]['value'] = group.get('value', 0.0)

        # Get movements in the selected range
        moves_domain = [
            ('product_id', 'in', products.ids),
            ('date', '>=', py_datetime.combine(date_from, py_datetime.min.time())),
            ('date', '<=', py_datetime.combine(date_to, py_datetime.max.time()))
        ]
        layers = self.env['stock.valuation.layer'].search(moves_domain, order='date asc, id asc')

        # Process data for each product
        records = []
        for product in products.sorted('name'):
            opening_bal = opening_balances[product.id]
            running_qty = opening_bal['qty']
            running_value = opening_bal['value']

            product_lines = []
            for layer in layers.filtered(lambda l: l.product_id.id == product.id):
                is_in = layer.quantity > 0
                move = layer.stock_move_id

                line_data = {
                    'date': layer.date.date(),
                    'movement_type': move.picking_type_id.display_name if move.picking_type_id else _(
                        'Inventory Adjustment'),
                    'reference': move.reference or '',
                    'mtno': move.picking_id.name if move.picking_id else '',
                    'in_qty': layer.quantity if is_in else 0.0,
                    'out_qty': -layer.quantity if not is_in else 0.0,
                    'price': layer.unit_cost,
                    'total': layer.value,
                    'uom': product.uom_id.name,
                }
                product_lines.append(line_data)

                running_qty += layer.quantity
                running_value += layer.value

            # Only add product to report if it has balance or movements
            if opening_bal['qty'] != 0 or product_lines:
                records.append({
                    'product': product,
                    'opening_qty': opening_bal['qty'],
                    'opening_total': opening_bal['value'],
                    'closing_qty': running_qty,
                    'closing_total': running_value,
                    'currency': product.currency_id or self.env.company.currency_id,
                    'lines': product_lines,
                })

        return {
            'doc_ids': docids,
            'doc_model': 'stock.movement.report.wizard',
            'data': {
                'category_name': category_name,
                'date_from': date_from_str,
                'date_to': date_to_str,
            },
            'records': records,  # The data key the template will use
        }