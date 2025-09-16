# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class CreateInvoice(models.Model):
    _name = "create.invoice"
    _description = "Client Invoice"

    def action_create_invoice(self):
        admission_id = self.env['student.admission'].browse(self._context.get('active_id'))
        if admission_id:
            sale_journals = self.env['account.journal'].sudo().search([('type', '=', 'sale')])
            invoice = self.env['account.move'].create({
                'invoice_origin': admission_id.name or '',
                'move_type': 'out_invoice',
                'ref': admission_id.name or '',
                'journal_id': sale_journals and sale_journals[0].id or False,
                'partner_id': admission_id.student_id.id,
                'invoice_date': fields.date.today(),
                'currency_id': admission_id.student_id.currency_id.id or self.env.user.currency_id.id,
                'company_id': self.env.user.company_id.id or False,
                'student_admission_id': admission_id.id or '',
            })

            # # Calculate quantity in months based on duration and a predefined number of days per month
            # days_per_month = 31  # Adjust this value as needed
            # invoice_line_quantity = (admission_id.duration + days_per_month - 1) // days_per_month

            if admission_id.package_line_id and admission_id.package_id:
                invoice.write({'invoice_line_ids': [
                    (0, 0, {
                        'product_id': admission_id.package_line_id.product_id.product_variant_id.id,
                        'name': admission_id.package_line_id.name or '',
                        # 'product_uom_id': admission_id.sport_id.uom_id.id,
                        'price_unit': admission_id.package_line_id.price,
                        'quantity': 1,  # Use calculated quantity in months
                        'move_name': admission_id.name or '',
                    })]})
            if invoice:
                admission_id.is_invoiced = True
        else:
            raise ValidationError('Admission Registration not found!')
