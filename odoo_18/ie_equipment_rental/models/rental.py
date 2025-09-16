from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EquipmentRentalLine(models.Model):
    _name = "equipment.rental.line"
    _description = "Equipment Rental Line"

    rental_id = fields.Many2one('equipment.rental', string="Rental Contract", ondelete='cascade')
    product_id = fields.Many2one('equipment.equipment', string="Equipment", required=True)
    days_count = fields.Integer(string="Days", related='rental_id.days_count', store=True)
    price_per_day = fields.Float(string="Price per Day", store=True)
    tax_id = fields.Many2many('account.tax', string="Taxes")
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends('days_count', 'price_per_day')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.days_count * rec.price_per_day * (1 + (rec.tax_id.amount / 100) if rec.tax_id else 1)






class EquipmentRental(models.Model):
    _name = "equipment.rental"
    _description = "Equipment Rental Contract"

    name = fields.Char(string="Contract Reference", required=True, copy=False, readonly=True, default=lambda self: _("New"))
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    days_count = fields.Integer(string="Days", compute="_compute_days", store=True)
    equipment_line_ids = fields.One2many('equipment.rental.line', 'rental_id', string="Equipment Lines")
    total_amount = fields.Float(string="Total", compute="_compute_total", store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string="Status", default="draft")

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("equipment.rental") or _("New")
        return super().create(vals)

    @api.depends('start_date', 'end_date')
    def _compute_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.days_count = (rec.end_date - rec.start_date).days + 1
            else:
                rec.days_count = 0

    @api.depends('equipment_line_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.mapped('equipment_line_ids.subtotal'))

    # Workflow Buttons
    def action_confirm(self):
        for rec in self:
            unavailable = rec.equipment_line_ids.filtered(lambda l: not l.product_id.is_available)
            if unavailable:
                unavailable_names = [line.product_id.product_id.name for line in unavailable]
                raise UserError(
                    _("The following equipment is not available: %s") % ', '.join(unavailable_names)
                )

            rec.state = "active"
            for line in rec.equipment_line_ids:
                line.product_id.is_available = False

    def action_done(self):
        for rec in self:
            rec.state = "done"
            for line in rec.equipment_line_ids:
                line.product_id.is_available = True

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
            for line in rec.equipment_line_ids:
                line.product_id.is_available = True

    def action_set_draft(self):
        for rec in self:
            rec.state = "draft"

    # إنشاء فاتورة تلقائي لكل خط
    def create_invoice_from_rental(self):
        for rec in self:
            if rec.invoice_id:
                raise UserError(_("Invoice already created for this rental."))

            if not rec.partner_id.property_account_receivable_id:
                raise UserError(_("Customer '%s' has no Receivable account configured!") % rec.partner_id.display_name)

            invoice_lines = []

            for line in rec.equipment_line_ids:
                equipment = line.product_id
                product = equipment.product_id

                income_account = equipment.property_account_income_id or product.categ_id.property_account_income_categ_id
                if not income_account:
                    raise UserError(_("Product '%s' has no Income account configured!") % product.name)

                if not product.uom_id:
                    raise UserError(_("Product '%s' has no Unit of Measure configured!") % product.name)

                if line.days_count <= 0 or line.price_per_day <= 0:
                    continue

                invoice_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'quantity': line.days_count,
                    'price_unit': line.price_per_day,
                    'account_id': income_account.id,
                    'tax_ids': line.tax_id,  # ضع الضريبة إذا كانت مطلوبة
                    'product_uom_id': product.uom_id.id,
                }))

            if not invoice_lines:
                raise UserError(_("No valid invoice lines to create."))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'invoice_date': rec.start_date,
                'invoice_line_ids': invoice_lines,
            }

            invoice = self.env['account.move'].create(invoice_vals)
            rec.invoice_id = invoice.id


    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No invoice linked to this rental."))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }
