from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, time


class StockMovementReportWizard(models.TransientModel):
    _name = 'stock.movement.report.wizard'
    _description = 'Stock Movement Report Wizard'

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_id = fields.Many2one('product.category', string="Product Category")

    from datetime import datetime, time

    def _build_report_data(self):
        """تجهيز بيانات التقرير مع معالجة datetime/date"""

        # حوّل date_from و date_to لـ datetime
        date_from_dt = datetime.combine(self.date_from, time.min)
        date_to_dt = datetime.combine(self.date_to, time.max)

        docs = []

        products = self.product_ids
        if self.category_id:
            products |= self.env['product.product'].search([
                ('categ_id', 'child_of', self.category_id.id)
            ])
        products = products.sorted(key=lambda p: p.name)

        for product in products:
            lines = []

            # Opening Balance
            opening_balance = 0.0
            opening_value = 0.0

            # جلب كل الحركات قبل تاريخ البداية
            moves_before = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('date', '<', date_from_dt),
                ('state', '=', 'done'),
            ])

            for move in moves_before:
                qty = move.product_uom_qty
                value = qty * move.price_unit
                if move.location_dest_id.usage == 'internal':
                    opening_balance += qty
                    opening_value += value
                if move.location_id.usage == 'internal':
                    opening_balance -= qty
                    opening_value -= value

            # حساب السعر الحقيقي للوحدة
            opening_price = 0.0
            if opening_balance != 0:
                opening_price = opening_value / opening_balance

            lines.append({
                'date': self.date_from.strftime('%Y-%m-%d'),
                'reference': 'Opening Balance',
                'in_qty': 0.0,
                'out_qty': 0.0,
                'bal_qty': opening_balance,
                'uom': product.uom_id.name,
                'price': opening_price,  # السعر الحقيقي للوحدة
                'total': opening_value,  # القيمة الإجمالية الحقيقية
            })

            # Transactions in Period
            moves = self.env['stock.move.line'].search([
                ('product_id', '=', product.id),
                ('date', '>=', date_from_dt),
                ('date', '<=', date_to_dt),
                ('state', '=', 'done')
            ], order='date asc')

            balance_qty = opening_balance

            for move in moves:
                in_qty = out_qty = 0.0
                if move.location_dest_id.usage == 'internal' and move.location_id.usage != 'internal':
                    in_qty = move.qty_done
                    balance_qty += in_qty
                elif move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                    out_qty = move.qty_done
                    balance_qty -= out_qty

                unit_price = move.move_id.price_unit or product.standard_price
                total_price = unit_price * (in_qty or -out_qty)

                lines.append({
                    'date': move.date.strftime('%Y-%m-%d'),
                    'reference': move.reference or '',
                    'mtno_field': move.move_id.mtno_field,
                    'in_qty': in_qty,
                    'out_qty': out_qty,
                    'bal_qty': balance_qty,
                    'uom': product.uom_id.name,
                    'price': unit_price,
                    'total': total_price,
                })

            closing_balance = balance_qty
            closing_value = sum([line['total'] for line in lines])
            closing_price = lines[-1]['price'] if lines else 0.0

            lines.append({
                'date': self.date_to.strftime('%Y-%m-%d'),
                'reference': 'Closing Balance',
                'in_qty': 0.0,
                'out_qty': 0.0,
                'bal_qty': closing_balance,
                'uom': product.uom_id.name,
                'price': closing_price,
                'total': closing_value,
            })

            docs.append({
                'product_name': product.display_name,
                'product_code': product.default_code or '',
                'lines': lines,
            })

        return {
            'company_name': self.env.company.name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'docs': docs
        }

    def action_print_report(self):
        self.ensure_one()
        if not self.product_ids and not self.category_id:
            raise UserError(_("الرجاء اختيار منتج أو تصنيف على الأقل."))

        data = self._build_report_data()
        return self.env.ref('stock_movement_report.action_report_stock_movement').report_action(self, data=data)


class ReportStockMovement(models.AbstractModel):
    _name = 'report.stock_movement_report.stock_movement_report_template'
    _description = 'Stock Movement Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'data': data or {},
        }
