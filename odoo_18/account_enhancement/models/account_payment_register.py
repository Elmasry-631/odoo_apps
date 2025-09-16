from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    TAX_WHITELIST = ['1% WH', '0.5% WH', '3% WH', '5% WH']  # Centralized tax names
    free_account_code = ["01710603", "01710604", "01710605", "01710606", "01710607", "01710608",
                         "01710610", "01710609", "01710611", "01710612", "01710613", "01710614",
                         "01710617", "01710618", "01710619", "01710640", "01710641", "01710642",
                         "01710650", "01710651", "01710652", "01710653", "01710654", "01710660",
                         "01710661", "06370602","01710600","01710601","01710602","01710611",
                         "01710612","01710613","01710614",]

    invoice_line_ids = fields.Many2many('account.move.line')
    move_id = fields.Many2one('account.move')
    move_ids = fields.Many2many('account.move')
    is_withholding_tax = fields.Boolean(compute="_compute_is_withholding_tax")
    withholding_tax_ids = fields.Many2many('account.tax', compute="_compute_withholding_tax_ids")
    name_withholding_tax = fields.Char(compute="_compute_name_withholding_tax")
    egp_currency_id = fields.Many2one('res.currency', string="EGP Currency",
                                      default=lambda self: self.env.ref('base.EGP'))
    usd_currency_id = fields.Many2one('res.currency', string="USD Currency",
                                      default=lambda self: self.env.ref('base.USD'))
    approved_egp_amount = fields.Monetary(string="Approved EGP Amount", currency_field="egp_currency_id")
    approved_usd_amount = fields.Monetary(string="Approved USD Amount", currency_field="usd_currency_id")
    payment_difference_one = fields.Monetary(
        compute='_compute_payment_difference_one')

    def action_approved_amount(self):
        for rec in self:
            if rec.currency_id.name =="EGP":
                rec.amount = rec.approved_egp_amount

            elif rec.currency_id.name == "USD":
                rec.amount = rec.approved_usd_amount
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',  # Keeps it as a popup
        }

    @api.onchange('currency_id')
    def _change_journal(self):
        if not self.currency_id:
            return

        journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('name', 'in', ['CIB EGP', 'CIB USD $'])
        ])

        if self.currency_id.name == "EGP":
            self.journal_id = journal.filtered(lambda j: j.name == 'CIB EGP').id
        elif self.currency_id.name == "USD":
            self.journal_id = journal.filtered(lambda j: j.name == 'CIB USD $').id

    @api.depends('can_edit_wizard', 'amount', 'installments_mode')
    def _compute_payment_difference(self):
        price = 0
        for wizard in self:
            for  line in wizard.invoice_line_ids:
                price +=  line.price_total
            wizard.payment_difference = price- wizard.amount

    @api.onchange('currency_id')
    def _change_writeoff_account_id(self):
        if self.currency_id.name == "USD":
            self.writeoff_account_id = self.env['account.account'].search([('name','=','WITHHOLDING TAXES -US$')]).id
        elif self.currency_id.name == "EGP":
            self.writeoff_account_id = self.env['account.account'].search([('name','=','WITHHOLDING TAXES - LE')]).id


    # def action_create_payments(self):
    #     egp_currency = self.env["res.currency"].search([("name",'=','EGP')],limit=1)
    #     rate = self._get_currency_rate(self.currency_id, self.move_id.invoice_date)
    #     egp_rate =  self._get_currency_rate(egp_currency, self.move_id.invoice_date)
    #
    #     if self.is_withholding_tax:
    #         payables_account = self.env['account.account'].search([('account_type', '=', 'liability_payable')], limit=1)
    #         if not payables_account:
    #             raise ValidationError("Payables account not found. Please configure an account named 'Payables'.")
    #     res = super().action_create_payments()
    #
    #     # accounts = self.env["account.account"].search([('code', 'in', self.free_account_code)])
    #     accounts = self.env["account.account"].search([('is_free_account', '=', True)])
    #     free_journal = self.env["account.journal"].search(
    #         [('is_free_jornal', '=', 'True')], limit=1)
    #
    #     if not free_journal:
    #         raise UserError("Free Journal not found.")
    #
    #     amounts_grouped = {}
    #
    #     for rec in self.invoice_line_ids:
    #         move = rec.move_id
    #         if rec.account_id in accounts and move.status_in_payment == "in_payment":
    #             key = (move.currency_id.id, move.partner_id.id)
    #             if key not in amounts_grouped:
    #                 amounts_grouped[key] = {}
    #
    #             # جمع الحسابات المشتركة مع قيمها
    #             if rec.account_id.id not in amounts_grouped[key]:
    #                 amounts_grouped[key][rec.account_id.id] = 0.0
    #             amounts_grouped[key][rec.account_id.id] += rec.amount_currency
    #
    #     # إنشاء قيد واحد لكل مجموعة
    #     for group_key, accounts_data in amounts_grouped.items():
    #         currency_id, partner_id = group_key
    #         total_amount = sum(accounts_data.values())  # مجموع القيمة لجميع الحسابات
    #         if not total_amount:
    #             continue  # تجاهل القيود الفارغة
    #
    #         # invoice_date = self.env["account.move"].search([('partner_id', '=', partner_id)], limit=1).invoice_date
    #         invoice_date = self.move_ids[0].invoice_date
    #         # print("invoice_date", invoice_date)
    #         # raise ValidationError("AAAAAaa")
    #         currency = self.env["res.currency"].browse(currency_id)
    #
    #         line_ids = []
    #         # إضافة السطور المحاسبية الخاصة بكل حساب مع قيمته المجمعة
    #         for account_id, amount in accounts_data.items():
    #             line_ids.append((0, 0, {
    #                 'name': 'Free Consolidated Entry',
    #                 'account_id': account_id,
    #                 # 'debit': abs(amount) if amount > 0 else 0,
    #                 # 'credit': abs(amount) if amount < 0 else 0,
    #                 'currency_id': currency.id,
    #                 'amount_currency': amount,
    #             }))
    #             # إضافة الحساب المقابل
    #             line_ids.append((0, 0, {
    #                 'name': 'Offset',
    #                 'account_id': account_id,
    #                 # 'debit': abs(amount) if amount < 0 else 0,
    #                 # 'credit': abs(amount) if amount > 0 else 0,
    #                 'currency_id': currency.id,
    #                 'amount_currency': -amount,
    #             }))
    #
    #         # إنشاء القيد المحاسبي النهائي
    #         self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'partner_id': partner_id,
    #             'free_journal_move_id': self.move_id.id or self.move_ids[0].id,
    #             'ref': self.move_id.ref or self.move_ids[0].ref,
    #             'journal_id': free_journal.id,
    #             'date': invoice_date,
    #             'state': 'draft',
    #             'currency_id': currency.id,
    #             'line_ids': line_ids,
    #         })
    #
    #     return res

    def action_create_payments(self):
        egp_currency = self.env["res.currency"].search([("name", '=', 'EGP')], limit=1)
        rate = self._get_currency_rate(self.currency_id, self.move_id.invoice_date)
        egp_rate = self._get_currency_rate(egp_currency, self.move_id.invoice_date)

        if self.is_withholding_tax:
            payables_account = self.env['account.account'].search([('account_type', '=', 'liability_payable')], limit=1)
            if not payables_account:
                raise ValidationError("Payables account not found. Please configure an account named 'Payables'.")

        res = super().action_create_payments()

        accounts = self.env["account.account"].search([('is_free_account', '=', True)])
        free_journal = self.env["account.journal"].search([('is_free_jornal', '=', 'True')], limit=1)
        if not free_journal:
            raise UserError("Free Journal not found.")

        for rec in self.invoice_line_ids:
            move = rec.move_id
            if rec.account_id in accounts:
                currency = self.currency_id
                partner_id = move.partner_id.id
                account_id = rec.account_id.id
                project_id = rec.x_studio_many2one_field_c7_1iocuc1sk.id
                cost_center_id = rec.x_studio_cost_center.id

                if rec.is_amount:
                    if currency.id == self.env.ref("base.EGP", raise_if_not_found=False).id:
                        amount = rec.egp_amount
                    elif currency.id == self.env.ref("base.USD", raise_if_not_found=False).id:
                        amount = rec.usd_amount
                    else:
                        amount = rec.amount_currency
                else:
                    amount = rec.amount_currency

                if not amount:
                    continue

                invoice_date = self.move_ids[0].invoice_date

                line_ids = [
                    (0, 0, {
                        'name': 'Free Consolidated Entry',
                        'account_id': account_id,
                        'currency_id': currency.id,
                        'amount_currency': amount,
                        # 'x_studio_many2one_field_c7_1iocuc1sk': project_id,
                        # 'x_studio_cost_center': cost_center_id,
                    }),
                    (0, 0, {
                        'name': 'Offset',
                        'account_id': account_id,
                        'currency_id': currency.id,
                        'amount_currency': -amount,
                        'x_studio_many2one_field_c7_1iocuc1sk': project_id,
                        'x_studio_cost_center': cost_center_id,
                    }),
                ]

                self.env['account.move'].create({
                    'move_type': 'entry',
                    'partner_id': partner_id,
                    'free_journal_move_id': self.move_id.id or self.move_ids[0].id,
                    'ref': self.move_id.ref or self.move_ids[0].ref,
                    'journal_id': free_journal.id,
                    'date': invoice_date,
                    'state': 'draft',
                    'currency_id': currency.id,
                    'line_ids': line_ids,
                })

        return res

    @api.depends('withholding_tax_ids')
    def _compute_name_withholding_tax(self):
        for rec in self:
            rec.name_withholding_tax = ', '.join(rec.withholding_tax_ids.mapped('name')) if rec.withholding_tax_ids else ''

    @api.depends('invoice_line_ids.tax_ids')
    def _compute_withholding_tax_ids(self):
        for rec in self:
            rec.withholding_tax_ids = [(6, 0, rec._get_withholding_tax_ids().ids)]

    @api.depends('invoice_line_ids.tax_ids')
    def _compute_is_withholding_tax(self):
        for rec in self:
            rec.is_withholding_tax = bool(rec._get_withholding_tax_ids())

    def _get_withholding_tax_ids(self):
        """Helper function to fetch withholding tax IDs based on the predefined list."""
        return self.invoice_line_ids.mapped('tax_ids').filtered(lambda t: t.name in self.TAX_WHITELIST)

    @api.depends('currency_id', 'invoice_line_ids.tax_ids', 'invoice_line_ids.is_amount', 'move_id.currency_id',
                 'move_id.invoice_date')
    def _compute_payment_difference_one(self):
        """Computes the payment difference based on withholding tax."""
        for record in self:
            rate = record._get_currency_rate(record.currency_id, record.move_id.invoice_date)
            rate_egp = record._get_currency_rate(record.move_id.currency_id, record.move_id.invoice_date)

            if record.currency_id.name == "USD":
                record.payment_difference_one = sum(
                    (tax.amount / 100) * line.price_subtotal
                    for line in record.invoice_line_ids
                    for tax in line.tax_ids if tax.name in self.TAX_WHITELIST
                )

            elif record.currency_id.name == "EGP":
                record.payment_difference_one = sum(
                    (tax.amount / 100) * line.price_subtotal
                    for line in record.invoice_line_ids
                    for tax in line.tax_ids if tax.name in self.TAX_WHITELIST
                )

            # Handle currency conversion
            if record.currency_id.name == "EGP" and record.move_id.currency_id.name == "USD":
                record.payment_difference_one *= rate

            elif record.currency_id.name == "USD" and record.move_id.currency_id.name == "EGP":
                record.payment_difference_one /= rate_egp

    @api.onchange('invoice_line_ids', 'currency_id')
    def _onchange_amount(self):
        for wizard in self:
            wizard.amount = 0.0
            rate = self._get_currency_rate(wizard.currency_id, wizard.move_id.invoice_date)
            egp_rate = self._get_currency_rate(wizard.egp_currency_id, wizard.move_id.invoice_date)

            for line in wizard.invoice_line_ids:
                if line.is_amount:
                    usd_value = line.price_total * line.usd_percentage
                    egp_value = line.price_total * line.egp_percentage

                    if wizard.currency_id.name == 'USD':
                        if wizard.move_id.currency_id.name == "USD":
                            wizard.amount += usd_value
                        elif wizard.move_id.currency_id.name == 'EGP':
                            wizard.amount += usd_value / egp_rate

                    elif wizard.currency_id.name == 'EGP':
                        if wizard.move_id.currency_id.name == 'USD':
                            wizard.amount += egp_value * rate
                        elif wizard.move_id.currency_id.name == 'EGP':
                            wizard.amount += egp_value

    #
    # @api.depends('invoice_line_ids', 'invoice_line_ids.is_amount', 'currency_id')
    # def _compute_amount(self):
    #     for wizard in self:
    #         wizard.amount = 0.0
    #         rate = self._get_currency_rate(wizard.currency_id, wizard.move_id.invoice_date)
    #         egp_rate = self._get_currency_rate(wizard.egp_currency_id, wizard.move_id.invoice_date)
    #
    #         for line in wizard.invoice_line_ids:
    #             if line.is_amount:
    #                 usd_value = line.price_total * line.usd_percentage
    #                 egp_value = line.price_total * line.egp_percentage
    #                 # if wizard.move_id.currency_id.name == "USD" and wizard.currency_id.name == "EGP":
    #                 #     egp_value = line.total_with_tax * line.egp_percentage * rate
    #                 #     wizard.amount += usd_value * rate + egp_value
    #                 # else:
    #                 if wizard.currency_id.name == 'USD':
    #                     if self.move_id.currency_id.name == "USD":
    #                         wizard.amount += usd_value
    #                     elif self.move_id.currency_id.name == 'EGP':
    #                         wizard.amount += usd_value / egp_rate
    #
    #                 elif wizard.currency_id.name == 'EGP':
    #                     if self.move_id.currency_id.name == 'USD':
    #                         wizard.amount += egp_value * rate
    #                     elif self.move_id.currency_id.name == 'EGP':
    #                         wizard.amount += egp_value

    def _get_currency_rate(self, currency, date):
        """Helper method to fetch currency exchange rate."""
        if not currency or not date:
            return 1.0  # Default rate

        rate_record = currency.rate_ids.filtered(lambda r: r.name == date)
        return rate_record[0].company_rate if rate_record else 1.0

    @api.onchange('currency_id')
    def _change_payment_difference(self):
        """Adjusts payment difference based on currency conversion."""
        for wizard in self:
            egp_currency_id = wizard.invoice_line_ids.mapped('egp_currency_id')
            rate = self._get_currency_rate(egp_currency_id, wizard.move_id.invoice_date)

            if wizard.move_id.currency_id.name == 'USD' and wizard.currency_id.name == 'EGP':
                wizard.payment_difference *= rate
            elif wizard.move_id.currency_id.name == 'EGP' and wizard.currency_id.name == 'USD':
                wizard.payment_difference /= rate

    @api.model
    # def default_get(self, fields):
    #     result = super().default_get(fields)
    #
    #     move = self.env['account.move'].browse(self.env.context.get('active_id'))
    #     result['move_id'] = move.id if move else False
    #     result['invoice_line_ids'] = [(6, 0, move.invoice_line_ids.ids)] if move else []
    #     result['approved_egp_amount'] = move.approved_egp_amount if move else 0.0
    #     result['approved_usd_amount'] = move.approved_usd_amount if move else 0.0
    #     return result
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'account.move' and active_ids:
            moves = self.env['account.move'].browse(active_ids)
            invoice_lines = moves.mapped('invoice_line_ids')
            res['invoice_line_ids'] = [(6, 0, invoice_lines.ids)]
            res['move_ids'] = [(6, 0, moves.ids)]
            res['move_id'] = moves[0].id if moves else False

        return res



