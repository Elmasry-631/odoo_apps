from odoo import models, api, _, fields
from odoo.exceptions import UserError
from datetime import datetime as py_datetime, timedelta


class StockMovementReport(models.AbstractModel):
    _name = 'report.stock_valuation_report_ex.stock_movement_report_template'
    _description = 'Stock Movement and Valuation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        docs = self.env['stock.movement.report.wizard'].browse(docids)

        product_ids = data.get('product_ids') or docs.mapped('product_ids').ids
        category_id = data.get('category_id') or (docs.category_id.id if docs.category_id else False)

        # --- START OF THE FIX ---
        date_from_str = data.get('date_from') or docs.date_from
        date_to_str = data.get('date_to') or docs.date_to

        # Convert string dates to date objects to allow calculations
        date_from = fields.Date.from_string(date_from_str)
        date_to = fields.Date.from_string(date_to_str)
        # --- END OF THE FIX ---

        if not product_ids and not category_id:
            raise UserError(_("You must select at least one product or a product category."))

        # Build product domain
        product_domain = [('type', '=', 'product')]
        if product_ids:
            product_domain.append(('id', 'in', product_ids))
        elif category_id:
            product_domain.append(('categ_id', 'child_of', category_id))

        products = self.env['product.product'].search(product_domain)
        if not products:
            raise UserError(_("No products found for the selected criteria."))

        category_name = self.env['product.category'].browse(category_id).name if category_id else _("All Products")
        products_map = {p.id: p for p in products}

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
            opening_balances[prod_id]['qty'] = group['quantity']
            opening_balances[prod_id]['value'] = group['value']

        # Find movements in the selected range
        moves_domain = [
            ('product_id', 'in', products.ids),
            ('date', '>=', py_datetime.combine(date_from, py_datetime.min.time())),
            ('date', '<=', py_datetime.combine(date_to, py_datetime.max.time()))
        ]
        layers = self.env['stock.valuation.layer'].search(moves_domain, order='date asc, id asc')

        # Prefetch related move data for performance
        move_ids = layers.mapped('stock_move_id')
        moves_map = {
            m.id: {
                'ref': m.reference,
                'picking_type': m.picking_type_id.display_name,
                'partner': m.picking_id.partner_id.name,
                'mtno': m.picking_id.name,  # Assuming MTNO is the picking name
            } for m in move_ids
        }

        # Process data
        product_lines = {p.id: [] for p in products}
        running_balances = {pid: bal.copy() for pid, bal in opening_balances.items()}

        for layer in layers:
            prod_id = layer.product_id.id
            product = products_map[prod_id]
            move_info = moves_map.get(layer.stock_move_id.id, {})

            is_in = layer.quantity > 0
            line = {
                'date': layer.date,
                'movement_type': move_info.get('picking_type', _('Inventory Adjustment')),
                'reference': move_info.get('ref', ''),
                'mtno': move_info.get('mtno', ''),
                'in_qty': layer.quantity if is_in else 0.0,
                'out_qty': -layer.quantity if not is_in else 0.0,
                'uom': product.uom_id.name,
                'price': layer.unit_cost,
                'total': layer.value,
            }
            product_lines[prod_id].append(line)

            # Update running balance
            running_balances[prod_id]['qty'] += layer.quantity
            running_balances[prod_id]['value'] += layer.value

        # Prepare final records for the report
        records = []
        for product in products.sorted('name'):
            opening_bal = opening_balances[product.id]
            closing_bal = running_balances[product.id]
            lines = product_lines[product.id]

            # FIX: Only include products that have an opening balance or movements
            if opening_bal['qty'] != 0 or lines:
                records.append({
                    'product': product,
                    'opening_qty': opening_bal['qty'],
                    'opening_total': opening_bal['value'],
                    'closing_qty': closing_bal['qty'],
                    'closing_total': closing_bal['value'],
                    'currency': product.currency_id or self.env.company.currency_id,
                    'lines': lines,
                })

        return {
            'doc_ids': docids,
            'doc_model': 'stock.movement.report.wizard',
            'data': {
                'category_name': category_name,
                # Pass strings to the template for display
                'date_from': fields.Date.to_string(date_from),
                'date_to': fields.Date.to_string(date_to),
            },
            'docs': docs,
            'records': records,
        }