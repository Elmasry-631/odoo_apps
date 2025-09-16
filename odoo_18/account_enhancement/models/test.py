from odoo import api, fields, models
from odoo.exceptions import ValidationError
from contextlib import ExitStack, contextmanager


class AccountMove(models.Model):
    _inherit = 'account.move'

    code_id = fields.Many2one('partner.code')

    egp_currency_id = fields.Many2one('res.currency', string="EGP Currency", default=lambda self: self.env.ref('base.EGP'))
    usd_currency_id = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self.env.ref('base.USD'))
    approved_egp_amount = fields.Monetary(string="Approved EGP Amount", currency_field="egp_currency_id")
    approved_usd_amount = fields.Monetary(string="Approved USD Amount", currency_field="usd_currency_id")
    is_free_journal = fields.Boolean(default=True, copy=False)

    # def _change_status_in_payment:


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

            # for tax_line_vals in tax_results['tax_lines_to_add']:
            #     # raise ValidationError("AAAAAAAAAAAAAAA")
            #     if self.move_type != 'in_invoice':
            #         to_create.append({
            #             **tax_line_vals,
            #             'display_type': 'tax',
            #             'move_id': move.id,
            #         })

            for tax_line_vals, grouping_key, to_update in tax_results['tax_lines_to_update']:
                line = tax_line_vals['record']
                if is_write_needed(line, to_update):
                    line.write(to_update)

        if to_delete:
            self.env['account.move.line'].browse(to_delete).with_context(dynamic_unlink=True).unlink()
        if to_create:
            self.env['account.move.line'].create(to_create)

    @api.onchange('invoice_line_ids')
    def _adjust_journal_entries(self):
        """ Helper function to adjust journal entries for debit and credit values """
        for record in self:
            total_pay = record.invoice_line_ids.mapped('total_with_tax')
            with_holding_tax_amount = sum(record.invoice_line_ids.mapped('with_holding_tax_amount'))
            product_lines = record.line_ids.filtered(lambda l: l.display_type == 'product')
            total_price = sum(record.invoice_line_ids.mapped('price_total'))
            rate = 1.0
            if record.currency_id and record.invoice_date:
                rate_record = record.currency_id.rate_ids.filtered(lambda r: r.name == record.invoice_date)
                if rate_record:
                    rate = rate_record[0].company_rate

            if total_price > 0:
                for product_line in product_lines:
                    related_invoice_line = record.invoice_line_ids.filtered(
                        lambda l: l.product_id == product_line.product_id
                    )

                    if related_invoice_line and product_line.debit > 0:
                        total_related_price = related_invoice_line.total_with_tax
                        # debit_lines = record.line_ids.filtered(lambda l: l.debit > 0)

                        if record.currency_id.name == 'USD':
                            if product_line:
                                product_line.with_context(check_move_validity=False).write({'debit': (total_related_price + with_holding_tax_amount)})
                                product_line.with_context(check_move_validity=False).creat(0,0,{'debit':  with_holding_tax_amount})
                        elif record.currency_id.name == 'EGP':
                            if product_line:
                                product_line.with_context(check_move_validity=False).write({'debit': (total_related_price + with_holding_tax_amount)/ rate})
                for rec in record.line_ids:
                    if rec.account_id.account_type == "liability_payable":
                        if record.currency_id.name == 'USD':
                            rec.with_context(check_move_validity=False).write({'credit': (sum(total_pay) + with_holding_tax_amount)})
                        elif record.currency_id.name == 'EGP':
                            rec.with_context(check_move_validity=False).write({'credit': (sum(total_pay)+ with_holding_tax_amount) / rate})

    @api.model
    def create(self, vals):
        """ Override create method to adjust journal entries after creation """
        record = super(AccountMove, self).create(vals)
        record._adjust_journal_entries()
        return record

    def write(self, vals):
        """ Override write method to adjust journal entries after updates """
        res = super(AccountMove, self).write(vals)
        self._adjust_journal_entries()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    usd_amount = fields.Monetary(string="USD Amount", currency_field="usd_currency_id" , compute="_compute_usd_amount")
    usd_currency_id = fields.Many2one("res.currency", string="Currency" , compute= "_compute_usd_currency")
    egp_amount = fields.Monetary(string="EGP Amount", currency_field="egp_currency_id", compute="_compute_egp_amount")
    egp_currency_id = fields.Many2one("res.currency", string="Currency" , compute= "_compute_usd_currency", store=True)
    usd_percentage = fields.Float('USD %')
    egp_percentage = fields.Float('EGP %')
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
    TAX_WHITELIST = ['1% WH', '0.5% WH', '3% WH', '5% WH']  # Centralized tax names

    total_with_tax= fields.Monetary(string="Total With Tax" ,currency_field="currency_id" ,compute="_compute_total_with_tax")
    journal_id = fields.Many2one('account.journal', related='move_id.journal_id', store=True, readonly=False)

    with_holding_tax_amount = fields.Monetary(string="Total With Tax" ,currency_field="currency_id" ,compute="_compute_with_holding_tax_amount")
    def _compute_with_holding_tax_amount(self):
        """Computes the payment difference based on withholding tax."""
        for line in self:
            rate = line._get_currency_rate(line.currency_id, line.move_id.invoice_date)
            rate_egp = line._get_currency_rate(line.move_id.currency_id, line.move_id.invoice_date)

            if line.currency_id.name == "USD":
                line.with_holding_tax_amount = sum(
                    (tax.amount / 100) * line.price_subtotal
                    # for line in line.invoice_line_ids
                    for tax in line.tax_ids if tax.name in self.TAX_WHITELIST
                )

            elif line.currency_id.name == "EGP":
                line.with_holding_tax_amount = sum(
                    (tax.amount / 100) * line.price_subtotal
                    for line in line.invoice_line_ids
                    for tax in line.tax_ids if tax.name in self.TAX_WHITELIST
                )
                # Handle currency conversion
            if line.currency_id.name == "EGP" and line.move_id.currency_id.name == "USD":
                line.with_holding_tax_amount *= rate

            elif line.currency_id.name == "USD" and line.move_id.currency_id.name == "EGP":
                line.with_holding_tax_amount /= rate_egp

    def _get_currency_rate(self, currency, date):
        """Helper method to fetch currency exchange rate."""
        if not currency or not date:
            return 1.0  # Default rate

        rate_record = currency.rate_ids.filtered(lambda r: r.name == date)
        return rate_record[0].company_rate if rate_record else 1.0


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

    @api.depends('amount_currency', 'currency_rate', 'move_id.invoice_date','balance')
    def _compute_amount_egp_currency(self):
        for record in self:
            rate = 1.0  # Default rate to avoid NoneType errors
            if record.egp_currency_id:
                for currency in record.egp_currency_id.rate_ids:
                    if currency.name == record.move_id.invoice_date:
                        rate = currency.company_rate
                        break  # Stop loop when match is found

            record.amount_egp_currency = 0
            if record.currency_id.id == 1 :
                record.amount_egp_currency = record.amount_currency * rate
            elif record.currency_id.id == 74:
                record.amount_egp_currency = record.amount_currency


    @api.onchange('usd_percentage', 'journal_id')
    def _onchange_usd_percentage(self):
        self.egp_percentage = 0
        if self.journal_id.id == 21:
            self.egp_percentage = 1
        else:
            if self.usd_percentage:
                if not (0 <= self.usd_percentage <= 1):
                    raise ValidationError("The Percentage Must Be Between 1% To 100% (0.01 to 1 in decimal).")
                self.egp_percentage = 1 - self.usd_percentage

    @api.onchange('egp_percentage')
    def _onchange_egp_percentage(self):
        if self.egp_percentage:
            if not (0 <= self.egp_percentage <= 1):
                raise ValidationError("The Percentage Must Be Between 1% To 100% (0.01 to 1 in decimal).")
            self.usd_percentage = 1 - self.egp_percentage


    def _compute_usd_currency(self):
        self.usd_currency_id = self.env['res.currency'].search([('id', '=', 1)])
        self.egp_currency_id = self.env['res.currency'].search([('id', '=', 74)])

    @api.depends('usd_percentage', 'price_unit', 'currency_rate', 'currency_id', 'quantity')
    def _compute_usd_amount(self):
        for record in self:
            record.usd_amount = 0
            if record.currency_id.id == 1:
                record.usd_amount = record.usd_percentage * (record.total_with_tax * record.currency_rate) * record.quantity
            elif record.currency_id.id == 74 and record.currency_rate:
                record.usd_amount = record.usd_percentage * (record.total_with_tax / record.currency_rate) * record.quantity

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
            if record.currency_id.id == 1 and record.price_unit:
                record.egp_amount = record.egp_percentage * (record.total_with_tax * rate) * record.quantity
            elif record.currency_id.id == 74:
                record.egp_amount = record.egp_percentage * record.total_with_tax * record.quantity

