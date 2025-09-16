from odoo import fields, models, _,api
from odoo.exceptions import UserError


class CheckBoxFields(models.Model):
    _inherit = "crm.lead"
    _description = "Add Check Box Fields"

    STATUS_SELECTION = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    GetSpecifications = fields.Selection(STATUS_SELECTION, string="Get Specifications", default='pending')
    GetProjectLocation = fields.Selection(STATUS_SELECTION, string="Get Project Location", default='pending')
    SiteVisit = fields.Selection(STATUS_SELECTION, string="Site Visit", default='pending')
    GetConsultantName = fields.Selection(STATUS_SELECTION, string="Get Consultant Name", default='pending')
    GetSystemSupplierName = fields.Selection(STATUS_SELECTION, string="Get System Supplier Name", default='pending')
    FollowUpTechnicalOffer = fields.Selection(STATUS_SELECTION, string="Follow Up Technical Offer", default='pending')
    FollowUpConsultantApproval = fields.Selection(STATUS_SELECTION, string="Follow Up Consultant Approval",
                                                  default='pending')
    FollowUpSystemSupplierApproval = fields.Selection(STATUS_SELECTION, string="Follow Up System Supplier Approval",
                                                      default='pending')
    FinancialOfferFollowUp = fields.Selection(STATUS_SELECTION, string="Financial Offer Follow Up", default='pending')

    Specifications = fields.Many2many('product.template')
    notes = fields.Text()




    def action_sale_quotations_new(self):
        self.ensure_one()

        # الشرط: لو الـ Specifications فاضي → يمنع الكوتيشن
        if not self.Specifications:
            raise UserError(_("You must add products in Specifications before creating a quotation."))

        # استدعاء الطبيعي من CRM → Sale
        action = super().action_sale_quotations_new()

        # بعد ما يتفتح الكوتيشن نضيف المنتجات
        if action.get("context"):
            context = dict(action["context"])
            context["default_order_line"] = []
            for product in self.Specifications:
                context["default_order_line"].append((
                    0, 0, {
                        "product_id": product.product_variant_id.id,
                        "product_uom_qty": 1,
                        "price_unit": product.list_price,  # يضيف السعر الافتراضي
                    }
                ))
            action["context"] = context

        return action
