# -*- coding: utf-8 -*-
import base64
import logging
import tempfile
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# نحاول IfcOpenShell للـ .ifc، وإلا نعالج IFCXML بـ lxml/xml.etree
try:
    import ifcopenshell  # type: ignore
    from ifcopenshell.util import element as ifc_element  # type: ignore
    IFC_AVAILABLE = True
except Exception:
    IFC_AVAILABLE = False

try:
    from lxml import etree as ET
except Exception:  # pragma: no cover
    import xml.etree.ElementTree as ET  # type: ignore


class ImportIFCWizard(models.TransientModel):
    _name = "import.ifc.wizard"
    _description = "Import BIM IFC (.ifc / .ifcxml)"

    project_id = fields.Many2one("project.project", string="المشروع (Project)", required=True)
    file = fields.Binary(string="ملف IFC/IFCXML", required=True)
    filename = fields.Char(string="اسم الملف")
    quantity_key = fields.Selection(
        [
            ("NetVolume", "NetVolume"),
            ("NetArea", "NetArea"),
            ("Length", "Length"),
            ("Count", "Count (عناصر)"),
        ],
        string="كمية مستهدفة للتجميع",
        default="Count",
        help="المفتاح الكميّ الذي سيتم تجميعه من QTO/Quantities (إذا وُجد)."
    )

    def _summary_to_html(self, summary):
        # summary: dict(class_name -> {"count": n, "qty": v})
        rows = []
        for k, v in sorted(summary.items()):
            rows.append(f"<tr><td>{k}</td><td class='text-end'>{v.get('count',0)}</td><td class='text-end'>{v.get('qty',0)}</td></tr>")
        html = "<table class='table table-sm'><thead><tr><th>IFC Class</th><th>Count</th><th>Qty</th></tr></thead><tbody>%s</tbody></table>" % "".join(rows)
        return html

    def action_import(self):
        self.ensure_one()
        if not self.file or not self.filename:
            raise UserError(_("ارفع ملف IFC أو IFCXML أولاً."))

        data = base64.b64decode(self.file)
        name = (self.filename or "").lower()

        summary = defaultdict(lambda: {"count": 0, "qty": 0.0})

        # حالة IFCXML
        if name.endswith(".ifcxml"):
            try:
                root = ET.fromstring(data)
            except Exception as e:
                raise UserError(_("ملف IFCXML غير صالح: %s") % e)
            # عدّ العناصر حسب الوسم (Tag) كإحصاء بسيط
            for elem in root.iter():
                tag = elem.tag.split("}")[-1]
                if tag.startswith("Ifc") and not tag.endswith("Type"):
                    summary[tag]["count"] += 1
            # الكميّات التفصيلية في IFCXML تحتاج خرائط QTO؛ نكتفي بالإحصاء السريع هنا
            html = self._summary_to_html(summary)
            self.project_id.message_post(body=_("IFCXML Import Summary") + "<br/>" + html)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {"title": _("IFC Import"), "message": _("تم تحليل IFCXML (ملخص مرفق في تبادل الرسائل على المشروع)."), "type": "success"},
            }

        # حالة IFC (STEP) — نستخدم IfcOpenShell إن توفّر
        if name.endswith(".ifc"):
            if not IFC_AVAILABLE:
                raise UserError(
                    _("مكتبة IfcOpenShell غير متوفرة على الخادم.\n"
                      "رجاءً تثبيتها ثم إعادة المحاولة (pip install ifcopenshell).")
                )
            # احفظ مؤقتًا وافتح
            with tempfile.NamedTemporaryFile(suffix=".ifc", delete=True) as tmp:
                tmp.write(data)
                tmp.flush()
                try:
                    model = ifcopenshell.open(tmp.name)  # type: ignore
                except Exception as e:
                    raise UserError(_("تعذّر فتح ملف IFC: %s") % e)

            # نجمع حسب الصنف (IfcWall/IfcSlab/...)
            products = model.by_type("IfcProduct")  # type: ignore
            qkey = (self.quantity_key or "Count")

            for p in products:
                # استبعد العناصر الافتراضية/غير المُنشأة
                cls = p.is_a()  # type: ignore
                if not cls or not cls.startswith("Ifc"):
                    continue
                summary[cls]["count"] += 1
                # محاولة استخراج الكميّات من QTO
                qty_val = 0.0
                try:
                    qdict = ifc_element.get_psets(p, qtos_only=True)  # type: ignore
                    # qdict شكلها: {"BaseQuantities": {"NetVolume": 12.3, ...}, ...}
                    for qset in (qdict or {}).values():
                        if isinstance(qset, dict) and qkey in qset and isinstance(qset[qkey], (int, float)):
                            qty_val += float(qset[qkey])
                except Exception as e:
                    _logger.debug("IFC QTO read error on %s: %s", cls, e)
                summary[cls]["qty"] += qty_val

            html = self._summary_to_html(summary)
            self.project_id.message_post(body=_("IFC Import Summary (%s)") % qkey + "<br/>" + html)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {"title": _("IFC Import"), "message": _("تم تحليل IFC (ملخص مرفق في تبادل الرسائل على المشروع)."), "type": "success"},
            }

        # امتداد غير مدعوم
        raise UserError(_("امتداد الملف غير مدعوم. الرجاء رفع .ifc أو .ifcxml."))
