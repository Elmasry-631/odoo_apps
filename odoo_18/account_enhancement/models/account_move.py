from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from contextlib import ExitStack, contextmanager
from datetime import date


class AccountMove(models.Model):
    _inherit = 'account.move'
    TAX_WHITELIST = ['1% WH', '0.5% WH', '3% WH', '5% WH']  # Centralized tax names

    code_id = fields.Many2one('partner.code')

    egp_currency_id = fields.Many2one('res.currency', string="EGP Currency", default=lambda self: self.env.ref('base.EGP'))
    usd_currency_id = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self.env.ref('base.USD'))
    approved_egp_amount = fields.Monetary(string="Approved EGP Amount", currency_field="egp_currency_id")
    approved_usd_amount = fields.Monetary(string="Approved USD Amount", currency_field="usd_currency_id")
    is_free_journal = fields.Boolean(default=True, copy=False)
    patch_no = fields.Char(string="Patch No", compute='_compute_patch_no', store=True)
    amount_tax_signed = fields.Monetary(
        string='Tax Signed',
        compute='_compute_amount', store=True, readonly=True,
        currency_field='currency_id',
    )
    related_move_lines_count = fields.Integer(
        string='Journal Entries',
        compute='_compute_related_move_lines_count'
    )

    amount_residual_signed = fields.Monetary(
        string='Amount Due Signed',
        compute='_compute_amount', store=True,
        currency_field='currency_id',
    )
    rate_today = fields.Float(string="Rate To Day", compute="_computerate_today")
    currency_rate_id = fields.Many2one("res.currency", string="EGP Currency", compute="_compute_currency_rate_id")
    amount_due_today = fields.Float(compute="_compute_amount_due_today")
    usd_percentage = fields.Float('USD %', store=True)
    egp_percentage = fields.Float('EGP %', store=True)
    total_invoice_amount = fields.Monetary(string="Total Invoice")
    total_invoice_amount_egp = fields.Monetary(string="Total Invoice EGP", compute="_compute_total_invoice_amount_egp", store=True ,currency_field="egp_currency_id")
    total_invoice_amount_usd = fields.Monetary(string="Total Invoice USD",  compute="_compute_total_invoice_amount_usd", store=True ,currency_field="usd_currency_id")
    is_egp_currency = fields.Boolean()

    @api.depends('total_invoice_amount','egp_percentage', 'rate_today','matched_payment_ids')
    def _compute_total_invoice_amount_egp(self):
        egp_currency = self.env.ref('base.EGP')
        usd_currency = self.env.ref('base.USD')

        for rec in self:
            rec.total_invoice_amount_egp = 0.0
            if rec.total_invoice_amount and rec.egp_percentage and rec.currency_id == usd_currency:
                rec.total_invoice_amount_egp = (rec.total_invoice_amount * rec.egp_percentage) * rec.rate_today
            elif rec.total_invoice_amount and rec.egp_percentage and rec.currency_id == egp_currency:
                rec.total_invoice_amount_egp = (rec.total_invoice_amount * rec.egp_percentage)
            egp_payments = rec.matched_payment_ids.filtered(lambda p: p.currency_id == egp_currency)

            if egp_payments:
                rec.total_invoice_amount_egp = 0.0

    @api.depends('total_invoice_amount', 'usd_percentage', 'matched_payment_ids')
    def _compute_total_invoice_amount_usd(self):
        usd_currency = self.env.ref('base.USD')
        for rec in self:
            rec.total_invoice_amount_usd = (rec.total_invoice_amount * rec.usd_percentage)
            usd_payments = rec.matched_payment_ids.filtered(lambda p: p.currency_id == usd_currency)
            if usd_payments:
                rec.total_invoice_amount_usd = 0.0

    @api.onchange('egp_percentage')
    def _onchange_egp_percentage(self):
        for rec in self:
            if not 0 <= rec.egp_percentage <= 1:
                raise ValidationError("EGP Percentage must be between 0.00 and 1.00 (e.g., 0.7 = 70%)")
            rec.usd_percentage = 1.0 - rec.egp_percentage

    @api.onchange('usd_percentage')
    def _onchange_usd_percentage(self):
        for rec in self:
            if not 0 <= rec.usd_percentage <= 1:
                raise ValidationError("USD Percentage must be between 0.00 and 1.00 (e.g., 0.3 = 30%)")
            rec.egp_percentage = 1.0 - rec.usd_percentage

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        usd_currency = self.env.ref('base.USD')
        egp_currency = self.env.ref('base.EGP')
        for rec in self:
            if rec.currency_id == egp_currency:
                rec.is_egp_currency = True
                rec.egp_percentage = 1.0
                rec.usd_percentage = 0.0
            elif rec.currency_id == usd_currency:
                rec.is_egp_currency = False
                rec.egp_percentage = 0.0
                rec.usd_percentage = 1.0
    # amount_pay_egp =fields.Monetary (string='amount / today rate',
    #     compute='_compute_amount_pay_egp',
    #     currency_field='currency_rate_id',)

    # amount_usd = fields.Monetary(string="Amount Rate  USD", compute="_compute_amount_usd")
    # invoice_total_amount_today = fields.Monetary('Invoice Total Amount',currency_field='company_currency_id', compute='_compute_invoice_total_amount_today')

    # @api.depends('rate_today')
    # def _compute_invoice_total_amount_today(self):
    #     for rec in self:
    #         if rec.x_studio_invoice_total_amount > 0:
    #             rec.invoice_total_amount_today = rec.x_studio_invoice_total_amount / rec.rate_today if rec.rate_today else 1
    #         else:
    #             rec.invoice_total_amount_today = 0

    # @api.depends('rate_today', 'currency_rate_id')
    # def _compute_amount_usd(self):
    #     egp_currency = self.env.ref('base.EGP', raise_if_not_found=False)
    #
    #     for rec in self:
    #         rec.amount_usd = 0.0  # تأمين القيمة الافتراضية
    #
    #         if rec.currency_rate_id == egp_currency and rec.rate_today:
    #             rec.amount_usd = rec.amount_pay_egp / rec.rate_today

    @api.depends('currency_id')
    def _compute_currency_rate_id(self):
        egp_currency = self.env.ref("base.EGP", raise_if_not_found=False)
        usd_currency = self.env.ref("base.USD", raise_if_not_found=False)
        for rec in self:
            if rec.currency_id == usd_currency:
                rec.currency_rate_id = egp_currency
            else:
                rec.currency_rate_id = usd_currency
    def _computerate_today(self):
        egp_currency = self.env.ref('base.EGP')  # تأكد إن كود EGP موجود في العملات
        company_currency = self.env.company.currency_id
        today = date.today()

        for rec in self:
            # لو عملة الشركة هي نفسها EGP، يبقى السعر 1
            if company_currency == egp_currency:
                rec.rate_today = 1.0
            else:
                # احصل على سعر الجنيه مقابل عملة الشركة
                rate = egp_currency._get_rates(self.env.company, today).get(egp_currency.id)
                rec.rate_today = rate if rate else 1.0

    @api.depends('invoice_line_ids', 'invoice_line_ids.price_total', 'rate_today', 'currency_id')
    def _compute_amount_due_today(self):
        egp_currency = self.env.ref('base.EGP')
        for rec in self:
            rec.amount_due_today = 0.0
            if rec.rate_today and rec.currency_id == egp_currency:
                for line in rec.invoice_line_ids:
                    rec.amount_due_today += line.price_total / rec.rate_today
            else:
                rec.amount_due_today = sum(rec.invoice_line_ids.mapped('total_amount_due_egp')) * rec.rate_today

    # @api.depends('matched_payment_ids')
    # def _compute_amount_pay_egp(self):
    #     for rec in self:
    #         rec.amount_pay_egp = 0.0
    #         egp = rec.env.ref('base.EGP', raise_if_not_found=False)
    #         usd = rec.env.ref('base.USD', raise_if_not_found=False)
    #
    #         if rec.currency_id == usd and rec.rate_today:
    #             amount_payment_egp = sum(
    #                 pay.amount for pay in rec.matched_payment_ids if pay.currency_id == egp
    #             )
    #             # نحسب القيمة المتبقية بالدولار ثم نطرح المدفوع بالجنيه المصري
    #             residual_egp = abs(rec.amount_due_today)
    #             rec.amount_pay_egp = residual_egp - amount_payment_egp
        # for rec in self:
        #     rec.amount_pay_egp = 0.0  # البداية من صفر
        #     egp = rec.env.ref('base.EGP', raise_if_not_found=False)
        #     usd = rec.env.ref('base.USD', raise_if_not_found=False)
        #     amount_payment_egp= 0.0
        #     if rec.currency_id == usd and rec.rate_today:
        #         for line in rec.invoice_line_ids:
        #             if line.egp_percentage > 0:
        #                 for pay in rec.matched_payment_ids:
        #                     if pay.currency_id == egp.id:
        #                         amount_payment_egp += pay.amount
        #                 rec.amount_pay_egp = rec.amount_due_today - amount_payment_egp
        #     elif rec.currency_id == egp and rec.rate_today:
        #         for line in rec.invoice_line_ids:
        #             amount = abs(rec.amount_due_today - abs(rec.amount_residual_signed / rec.invoice_line_ids[0].currency_rate))
        #             x = amount + abs(rec.amount_residual_signed / rec.invoice_line_ids[0].currency_rate)
        #             rec.amount_pay_egp =   x -(sum(rec.matched_payment_ids.mapped('amount')) / rec.invoice_line_ids[0].currency_rate)



    @api.depends('invoice_date', 'name')
    def _compute_patch_no(self):
        for record in self:
            if record.date and record.name:
                # Format the date as DD/MM/YYYY
                date_str = record.date.strftime('%m/%d/%Y')
                # Get the last part of the invoice number after the last '/'
                serial_parts = record.name.split('/')
                serial_suffix = serial_parts[-1] if serial_parts else record.name
                # Set patch_no
                record.patch_no = f"{date_str} - {serial_suffix}"
            else:
                record.patch_no = ''

    @api.onchange('code_id')
    def change_partner(self):
        partners = self.env['res.partner'].search([('code_id','!=', False)])
        for partner in partners:
            if partner.code_id == self.code_id:
                self.partner_id = partner

    @contextmanager
    def _sync_tax_lines(self, container):
        AccountTax = self.env['account.tax']
        fake_base_line = AccountTax._prepare_base_line_for_taxes_computation(None)

        def get_base_lines(move):
            return move.line_ids.filtered(lambda line: line.display_type in ('product', 'epd', 'rounding', 'cogs'))

        def get_tax_lines(move):
            return move.line_ids.filtered('tax_repartition_line_id')

        def get_value(record, field):
            return self.env['account.move.line']._fields[field].convert_to_write(record[field], record)

        def get_tax_line_tracked_fields(line):
            return ('amount_currency', 'balance')

        def get_base_line_tracked_fields(line):
            grouping_key = AccountTax._prepare_base_line_grouping_key(fake_base_line)
            if line.move_id.is_invoice(include_receipts=True):
                extra_fields = ['price_unit', 'quantity', 'discount']
            else:
                extra_fields = ['amount_currency']
            return list(grouping_key.keys()) + extra_fields

        def field_has_changed(values, record, field):
            return get_value(record, field) != values.get(record, {}).get(field)

        def get_changed_lines(values, records, fields=None):
            return (
                record
                for record in records
                if record not in values
                or any(field_has_changed(values, record, field) for field in values[record] if not fields or field in fields)
            )

        def any_field_has_changed(values, records, fields=None):
            return any(record for record in get_changed_lines(values, records, fields))

        def is_write_needed(line, values):
            return any(
                self.env['account.move.line']._fields[fname].convert_to_write(line[fname], self) != values[fname]
                for fname in values
            )

        moves_values_before = {
            move: {
                field: get_value(move, field)
                for field in ('currency_id', 'partner_id', 'move_type')
            }
            for move in container['records']
            if move.state == 'draft'
        }
        base_lines_values_before = {
            move: {
                line: {
                    field: get_value(line, field)
                    for field in get_base_line_tracked_fields(line)
                }
                for line in get_base_lines(move)
            }
            for move in container['records']
        }
        tax_lines_values_before = {
            move: {
                line: {
                    field: get_value(line, field)
                    for field in get_tax_line_tracked_fields(line)
                }
                for line in get_tax_lines(move)
            }
            for move in container['records']
        }
        yield

        to_delete = []
        to_create = []
        for move in container['records']:
            if move.state != 'draft':
                continue

            tax_lines = get_tax_lines(move)
            base_lines = get_base_lines(move)
            move_tax_lines_values_before = tax_lines_values_before.get(move, {})
            move_base_lines_values_before = base_lines_values_before.get(move, {})
            if (
                move.is_invoice(include_receipts=True)
                and (
                    field_has_changed(moves_values_before, move, 'currency_id')
                    or field_has_changed(moves_values_before, move, 'move_type')
                )
            ):
                # Changing the type of an invoice using 'switch to refund' feature or just changing the currency.
                round_from_tax_lines = False
            elif changed_lines := list(get_changed_lines(move_base_lines_values_before, base_lines)):
                # A base line has been modified.
                round_from_tax_lines = (
                    # The changed lines don't affect the taxes.
                    all(not line.tax_ids and not move_base_lines_values_before.get(line, {}).get('tax_ids') for line in changed_lines)
                    # Keep the tax lines amounts if an amount has been manually computed.
                    or any_field_has_changed(move_tax_lines_values_before, tax_lines)
                )

                # If the move has been created with all lines including the tax ones and the balance/amount_currency are provided on
                # base lines, we don't need to recompute anything.
                if (
                    round_from_tax_lines
                    and any(line[field] for line in changed_lines for field in ('amount_currency', 'balance'))
                ):
                    continue
            elif any(line not in base_lines for line, values in move_base_lines_values_before.items() if values['tax_ids']):
                # Removed a base line affecting the taxes.
                round_from_tax_lines = any_field_has_changed(move_tax_lines_values_before, tax_lines)
            else:
                continue

            base_lines_values, tax_lines_values = move._get_rounded_base_and_tax_lines(round_from_tax_lines=round_from_tax_lines)
            AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines_values, move.company_id, include_caba_tags=move.always_tax_exigible)
            tax_results = AccountTax._prepare_tax_lines(base_lines_values, move.company_id, tax_lines=tax_lines_values)

            for base_line, to_update in tax_results['base_lines_to_update']:
                line = base_line['record']
                if is_write_needed(line, to_update):
                    line.write(to_update)

            for tax_line_vals in tax_results['tax_lines_to_delete']:
                to_delete.append(tax_line_vals['record'].id)

            for tax_line_vals in tax_results['tax_lines_to_add']:
                if tax_line_vals['name'] in  self.TAX_WHITELIST:
                    to_create.append({
                            **tax_line_vals,
                            'display_type': 'tax',
                            'move_id': move.id,
                        })

            for tax_line_vals, grouping_key, to_update in tax_results['tax_lines_to_update']:
                line = tax_line_vals['record']
                if is_write_needed(line, to_update):
                    line.write(to_update)

        if to_delete:
            self.env['account.move.line'].browse(to_delete).with_context(dynamic_unlink=True).unlink()
        if to_create:
            self.env['account.move.line'].create(to_create)

    def _post(self, soft=True):
        self.invoice_line_ids._compute_amount_currency()
        return  super()._post()

    def button_draft(self):
        res = super().button_draft()
        self.invoice_line_ids._compute_amount_currency()
        return res

    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0
            amount_tax = 0.0
            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        amount_tax += line.amount_currency
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign
            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_untaxed_in_currency_signed = -total_untaxed_currency
            move.amount_tax_signed = -amount_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)


    def action_view_all_related_move_lines(self):
        self.ensure_one()

        move_ids = [self.id]  # قيد الـ Bill

        # قيد الـ Payments
        payment_moves = self.env['account.payment'].search([('invoice_ids', 'in', self.id)])
        move_ids += payment_moves.mapped('move_id').ids

        move_ids.append(self.free_journal_move_id.id)

        # فتح شاشة account.move.line
        return {
            'name': 'Related Journal Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': ['|',('move_id', 'in', move_ids),('move_id.free_journal_move_id','=',self.id)],
            'target': 'current',
        }
        # move_ids_from_payments = self.payment_ids.mapped('move_id').ids if hasattr(self, 'payment_ids') else []
        # move_ids_from_ref = self.env['account.move'].search([('ref', '=', self.ref or self.name)]).ids if self.ref else []
        #
        # all_move_ids = list(set(move_ids_from_payments + move_ids_from_ref))
        #
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Journal Entries',
        #     'res_model': 'account.move.line',
        #     'view_mode': 'list,form',
        #     'views': [
        #         (self.env.ref('account.view_move_line_tree').id, 'list'),
        #         (self.env.ref('account.view_move_line_form').id, 'form')
        #     ],
        #     'domain': [('move_id', 'in', all_move_ids)],
        #     'context': {'create': False},
        # }

    def _compute_related_move_lines_count(self):
        for rec in self:
            move_ids = [rec.id]

            payment_moves = self.env['account.payment'].search([('invoice_ids', 'in', rec.id)])
            move_ids += payment_moves.mapped('move_id').ids

            if rec.free_journal_move_id:
                move_ids.append(rec.free_journal_move_id.id)

            journal_lines_count = self.env['account.move.line'].search_count(['|',('move_id', 'in', move_ids),('move_id.free_journal_move_id','=',self.id)])
            rec.related_move_lines_count = journal_lines_count

    def action_open_partner_ledger(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_partner_ledger")
        action['params'] = {
            'options': {
                'partner_ids': [self.partner_id.id],
                'unfold_all': True,
            },
            'ignore_session': True,
        }
        return action


    @api.depends('line_ids.amount_residual', 'line_ids.amount_residual_currency', 'line_ids.balance',
                 'line_ids.amount_currency',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.origin_payment_id.is_matched',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.origin_payment_id.is_matched',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.balance',
                 'line_ids.currency_id',
                 'line_ids.amount_currency',
                 'line_ids.amount_residual',
                 'line_ids.amount_residual_currency',
                 'line_ids.payment_id.state',
                 'line_ids.full_reconcile_id',
                 'state'
                 )
    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0

            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign

            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_untaxed_in_currency_signed = -total_untaxed_currency
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)

            if move.currency_id.name == 'EGP':
                move.amount_residual_signed = total_residual_currency
            elif move.currency_id.name == 'USD':
                move.amount_residual_signed = total_residual_currency
            else:
                move.amount_residual_signed = total_residual_currency
    free_journal_move_id  = fields.Many2one('account.move')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    TAX_WHITELIST = ['1% WH', '0.5% WH', '3% WH', '5% WH']  # Centralized tax names
    usd_amount = fields.Monetary(string="USD Amount", currency_field="usd_currency_id" , compute="_compute_usd_amount")
    usd_currency_id = fields.Many2one("res.currency", string="Currency" , compute= "_compute_usd_currency")
    egp_amount = fields.Monetary(string="EGP Amount", currency_field="egp_currency_id", compute="_compute_egp_amount")
    egp_currency_id = fields.Many2one("res.currency", string="Currency" , compute= "_compute_usd_currency", store=True)
    usd_percentage = fields.Float('USD %', related="move_id.usd_percentage")
    egp_percentage = fields.Float('EGP %', related="move_id.egp_percentage")
    invoice_date = fields.Date(related="move_id.invoice_date")
    amount_egp_currency = fields.Monetary(string=" Amount Currency EGP", currency_field="egp_currency_id", compute="_compute_amount_egp_currency")
    line_amount_tax = fields.Monetary(string=" Amount Tax", currency_field="currency_id",compute="_compute_amount_tax")
    amount_all_tax = fields.Monetary(string=" Amount all Tax", currency_field="currency_id",compute="_compute_amount_tax")
    is_amount = fields.Boolean(string="is Pay")
    new_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='account_move_line_new_tax_rel',  # Custom table name
        column1='move_line_id',  # Reference to the current model
        column2='tax_id',  # Reference to the related model
        string="Taxes",
        compute='_compute_new_tax_ids', store=True, readonly=False, precompute=True,
        context={'active_test': False},
        check_company=True,
        tracking=True,

    )

    total_with_tax= fields.Monetary(string="Total With Tax" ,currency_field="currency_id" ,compute="_compute_total_with_tax")
    journal_id = fields.Many2one('account.journal', related='move_id.journal_id', store=True, readonly=False)

    total_amount_due_egp = fields.Float(compute="_compute_total_amount_due_egp", string="Total Amount Due in EGP")

    @api.constrains('account_id','tax_ids')
    def _set_feat_and_cost_center(self):
        accounts = ['01010604', '01010605', '02270611', '02270610']
        feat = self.env["x_feat"].search([('x_name', '=', '0000')], limit=1)
        cost_center = self.env["x_cost_center"].search([('x_name', '=', '00000')], limit=1)

        for rec in self:
            if rec.account_id and rec.account_id.code in accounts:
                rec.x_studio_many2one_field_c7_1iocuc1sk = feat
                rec.x_studio_cost_center = cost_center

    @api.depends('price_total', 'egp_percentage')
    def _compute_total_amount_due_egp(self):
        for rec in self:
            rec.total_amount_due_egp = (rec.price_total or 0.0) * (rec.egp_percentage or 0.0)

    # @api.depends('total_with_tax')
    # def _compute_amount_currency(self):
    #    res = super()._compute_amount_currency()
    #    for line in self:
    #        if line.move_type == 'entry':
    #            line.amount_currency = line.total_with_tax
    #    return res
    #
    # @api.depends('total_with_tax')
    # def _compute_amount_currency(self):
    #     for line in self:
    #      if line.move_type == 'entry':
    #         line.amount_currency = line.total_with_tax
    #      else:
    #         # استدعاء الدالة الأصلية فقط إذا النوع مش entry
    #         super(type(line), line)._compute_amount_currency()


    @api.depends('tax_ids')
    def _compute_new_tax_ids(self):
        self.new_tax_ids = self.tax_ids

    @api.depends("price_subtotal", "line_amount_tax", "new_tax_ids")
    def _compute_total_with_tax(self):
        for rec in self:
            rec.total_with_tax = rec.price_subtotal  # Start with subtotal
            for tax in rec.new_tax_ids:
                if tax.name not in ['1% WH','0.5% WH','3% WH','5% WH']:
                    rec.total_with_tax += rec.line_amount_tax  # Add tax amount


    @api.onchange('new_tax_ids')
    def set_taxs(self):
        for rec in self:
                rec.tax_ids = rec.new_tax_ids

    @api.depends('new_tax_ids', 'price_subtotal')
    def _compute_amount_tax(self):
        for rec in self:
             rec.line_amount_tax = sum((tax.amount / 100) * rec.price_subtotal for tax in rec.new_tax_ids if tax.name not in ['1% WH', '0.5% WH', '3% WH', '5% WH'])
             rec.amount_all_tax =  sum((tax.amount / 100) * rec.price_subtotal for tax in rec.new_tax_ids)


    @api.depends('product_id', 'product_uom_id')
    def _compute_tax_ids(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note', 'payment_term') or line.is_imported:
                continue
            # /!\ Don't remove existing taxes if there is no explicit taxes set on the account.
            if line.product_id or (line.display_type != 'discount' and (line.account_id.tax_ids or not line.tax_ids)):
                line.tax_ids = line._get_computed_taxes()
    #
    # @api.depends('amount_currency', 'currency_rate', 'move_id.invoice_date','balance')
    # def _compute_amount_egp_currency(self):
    #     for record in self:
    #         rate = 1.0  # Default rate to avoid NoneType errors
    #         if record.egp_currency_id:
    #             print("rate111111111", rate)
    #
    #             for currency in record.egp_currency_id.rate_ids:
    #                 if currency.name == record.move_id.invoice_date:
    #                     print("rate2222222", rate)
    #                     rate = currency.company_rate
    #                     break  # Stop loop when match is found
    #
    #         record.amount_egp_currency = 0
    #         print("rate", rate)
    #         raise ValidationError("AAA")
    #         if record.currency_id == self.env.ref('base.USD') :
    #             record.amount_egp_currency = record.amount_currency * rate
    #         elif record.currency_id == self.env.ref('base.EGP'):
    #             record.amount_egp_currency = record.amount_currency

    @api.depends('amount_currency', 'currency_rate', 'move_id.invoice_date', 'balance')
    def _compute_amount_egp_currency(self):
        for record in self:
            rate = 1.0

            if record.egp_currency_id:
                for currency in record.egp_currency_id.rate_ids:
                    if record.move_type == 'entry':
                        if currency.name == record.move_id.date:
                            rate = currency.company_rate
                    if record.move_type in ['in_invoice', 'in_refund']:
                        if currency.name == record.move_id.invoice_date:
                            rate = currency.company_rate

                        break

            record.amount_egp_currency = 0
            if record.currency_id == self.env.ref('base.USD'):
                record.amount_egp_currency = record.amount_currency * rate
            elif record.currency_id == self.env.ref('base.EGP'):
                record.amount_egp_currency = record.amount_currency


    # @api.onchange('usd_percentage', 'journal_id')
    # def _onchange_usd_percentage(self):
    #     self.egp_percentage = 0
    #     if self.journal_id.id == 21:
    #         self.egp_percentage = 1
    #     else:
    #         if self.usd_percentage:
    #             if not (0 <= self.usd_percentage <= 1):
    #                 raise ValidationError("The Percentage Must Be Between 1% To 100% (0.01 to 1 in decimal).")
    #             self.egp_percentage = 1 - self.usd_percentage

    # @api.onchange('egp_percentage')
    # def _onchange_egp_percentage(self):
    #     if self.egp_percentage:
    #         if not (0 <= self.egp_percentage <= 1):
    #             raise ValidationError("The Percentage Must Be Between 1% To 100% (0.01 to 1 in decimal).")
    #         self.usd_percentage = 1 - self.egp_percentage


    def _compute_usd_currency(self):
        # Replace direct ID search with env.ref() for better maintainability
        self.usd_currency_id = self.env.ref('base.USD')
        self.egp_currency_id = self.env.ref('base.EGP')

    @api.depends('usd_percentage', 'price_unit', 'currency_rate', 'currency_id', 'quantity')
    def _compute_usd_amount(self):
        for record in self:
            record.usd_amount = 0
            if record.currency_id == self.env.ref('base.USD'):
                record.usd_amount = record.usd_percentage * (record.total_with_tax * record.currency_rate)
            elif record.currency_id == self.env.ref('base.EGP') and record.currency_rate:
                record.usd_amount = record.usd_percentage * (record.total_with_tax / record.currency_rate)

    @api.depends('egp_percentage', 'price_unit', 'currency_id', 'quantity', 'invoice_date')
    def _compute_egp_amount(self):
        for record in self:
            rate = 1.0  # Default rate to avoid NoneType errors
            if record.egp_currency_id:
                for currency in record.egp_currency_id.rate_ids:
                    if currency.name == record.move_id.invoice_date:
                        rate = currency.company_rate
                        break  # Stop loop when match is found

            record.egp_amount = 0
            if record.currency_id == self.env.ref('base.USD') and record.price_unit:
                record.egp_amount = record.egp_percentage * (record.total_with_tax * rate)
            elif record.currency_id == self.env.ref('base.EGP'):
                record.egp_amount = record.egp_percentage * record.total_with_tax


    # @api.depends('move_id','account_id')
    # def _compute_display_type(self):
    #     for line in self.filtered(lambda l: not l.display_type):
    #         # avoid cyclic dependencies with _compute_account_id
    #         account_set = self.env.cache.contains(line, line._fields['account_id'])
    #         tax_set = self.env.cache.contains(line, line._fields['tax_line_id'])
    #         line.display_type = (
    #             'tax' if tax_set and line.tax_line_id else
    #             'payment_term' if account_set and line.account_id.account_type in ['asset_receivable', 'liability_payable'] else
    #             'product'
    #         ) if line.move_id.is_invoice() else 'product'
    #     for rec in self:
    #         if rec.account_id.account_type == 'liability_payable':
    #             rec.display_type = 'payment_term'

    @api.constrains('currency_id', 'tax_ids')
    def _check_currency_tax_combination(self):
        egp_tax_account = self.env['account.account'].search([('code', '=', '02270611')])
        usd_tax_account = self.env['account.account'].search([('code', '=', '02270610')])
        for line in self:
            for tax in line.tax_ids:
                if tax.name in line.TAX_WHITELIST:
                    line.amount_currency = line.total_with_tax
                    for account in  tax.invoice_repartition_line_ids:
                        if account.repartition_type == "tax":
                            if account.account_id != egp_tax_account or account.account_id != usd_tax_account :
                                if line.currency_id.name =="EGP":
                                    account.account_id = egp_tax_account
                                elif line.currency_id.name =="USD":
                                    account.account_id = usd_tax_account

    def action_register_payment(self, ctx=None):
        ''' Open the account.payment.register wizard to pay the selected journal items.
        :return: An action opening the account.payment.register wizard.
        '''
        # افتراضًا إن كل الأسطر تخص نفس الفاتورة
        move_ids = self.mapped('move_id').ids
        context = {
            'active_model': 'account.move',
            'active_ids': move_ids,
        }
        if ctx:
            context.update(ctx)
        return {
            'name': _('Pay'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

