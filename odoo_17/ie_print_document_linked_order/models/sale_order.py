from odoo import models, api
from odoo.exceptions import UserError
import base64
import io
import logging
from PyPDF2 import PdfMerger

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_product_attachments(self):
        """عرض مرفقات المنتجات المرتبطة بأمر البيع"""
        self.ensure_one()
        product_ids = self.order_line.product_id.product_tmpl_id.ids

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attachments',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,kanban,form',
            'domain': [
                ('res_model', '=', 'product.template'),
                ('res_id', 'in', product_ids)
            ],
            'context': {'create': False},
            'target': 'current',
        }


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def action_print_selected(self, attachment_ids):
        """دمج ملفات PDF المحددة في ملف واحد"""
        attachments = self.browse(attachment_ids)
        merger = PdfMerger()

        for attachment in attachments:
            if attachment.mimetype == 'application/pdf' and attachment.datas:
                try:
                    pdf_content = base64.b64decode(attachment.datas)
                    if pdf_content.strip():  # الملف مش فاضي
                        merger.append(io.BytesIO(pdf_content))
                except Exception as e:
                    _logger.warning(
                        f"Skipped invalid PDF: {attachment.name}, error: {e}"
                    )
            else:
                _logger.info(
                    f"Attachment {attachment.name} is not a valid PDF or has no data."
                )

        if not merger.pages:
            raise UserError("No valid PDF files found to merge!")

        output = io.BytesIO()
        merger.write(output)
        merger.close()

        return {
            'type': 'ir.actions.act_url',
            'url': f"web/content/?model=ir.attachment&id={attachments[0].id}&field=datas&download=true&filename=merged.pdf",
            'target': 'new',
        }
