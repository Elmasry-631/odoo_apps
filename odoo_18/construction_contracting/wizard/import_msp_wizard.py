# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree  # اضف lxml إلى البيئة لو غير موجود

class ImportMSPWizard(models.TransientModel):
    _name = "import.msp.wizard"
    _description = "Import Microsoft Project XML"

    file = fields.Binary(string="MS Project XML", required=True)
    filename = fields.Char(string="File name")

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("رفع ملف XML أولاً."))
        xml_bytes = self.file.decode('base64') if isinstance(self.file, bytes) else self.file
        try:
            root = etree.fromstring(xml_bytes)
        except Exception as e:
            raise UserError(_("XML غير صالح: %s") % e)

        # مثال مبسّط: عدّ المهام فقط (Tasks/Task)
        ns = root.nsmap.get(None) or ""
        tasks = root.findall(".//{%s}Tasks/{%s}Task" % (ns, ns))
        # TODO: أنشئ/حدّث project.task والعلاقات
        return {"type": "ir.actions.client", "tag": "display_notification",
                "params": {"title": _("MSP Import"), "message": _("عدد المهام: %s") % len(tasks), "type": "success"}}
