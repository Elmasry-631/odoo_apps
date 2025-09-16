# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# نحاول استخدام lxml، ونfallback إلى xml.etree إن لم تتوفر
try:
    from lxml import etree as ET
except Exception:  # pragma: no cover
    import xml.etree.ElementTree as ET  # type: ignore


def _try_parse_dt(s):
    """يحاول قراءة التاريخ/الوقت من نصّ (ISO أو صيغ P6 شائعة)."""
    if not s:
        return False
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            continue
    # محاولة أخيرة: fromisoformat إن توفّر
    try:
        return datetime.fromisoformat(s.strip())
    except Exception:
        return False


class ImportP6Wizard(models.TransientModel):
    _name = "import.p6.wizard"
    _description = "Import Primavera P6 (XML)"

    project_id = fields.Many2one(
        "project.project", string="المشروع (Project)", required=True
    )
    file = fields.Binary(string="ملف P6 XML", required=True, help="ملف تمّ تصديره من P6 بصيغة XML (p6apibo.xsd).")
    filename = fields.Char("اسم الملف")
    prefix_code_in_name = fields.Boolean(
        string="سابق الكود داخل اسم المهمة",
        default=True,
        help="لو مُفعّل: سيظهر (ActivityId - Name) في اسم المهمة."
    )
    import_relationships = fields.Boolean(
        string="استيراد العلاقات (FS/SS/FF/SF) إن أمكن",
        default=True,
        help="يتطلب وجود حقل علاقات على project.task (مثلاً predecessor_ids)."
    )

    def _findall_any(self, root, paths):
        """يساعد في العثور على نودز مع اختلاف الأسماء/المسارات بين إصدارات P6."""
        for p in paths:
            try:
                found = root.findall(p)
                if found:
                    return found
            except Exception:
                continue
        return []

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("ارفع ملف XML أولاً."))

        xml_bytes = base64.b64decode(self.file)
        try:
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            raise UserError(_("XML غير صالح: %s") % e)

        ProjectTask = self.env["project.task"].sudo()
        has_pred_field = "predecessor_ids" in ProjectTask._fields  # إن كان لديك حقل للعلاقات
        created, updated = 0, 0

        # جمع الأنشطة (Activities/Activity) — أسماء العناصر تختلف حسب إصدار P6، لذلك نحاول عدة مسارات
        activities = self._findall_any(
            root,
            [
                ".//Activities/Activity",
                ".//Activity",
                ".//Project/Activities/Activity",
            ],
        )
        # علاقات (Relationships/Relationship)
        rels = self._findall_any(
            root,
            [
                ".//Relationships/Relationship",
                ".//Relationship",
                ".//Project/Relationships/Relationship",
            ],
        )

        # خرائط لمطابقة العلاقات لاحقًا
        id_to_task = {}

        for a in activities:
            # نحاول قراءة المعرف والاسم والتواريخ من أكثر من اسم عنصر
            aid = (a.findtext("Id") or a.findtext("ActivityId") or a.findtext("ObjectId") or "").strip()
            aname = (a.findtext("Name") or "").strip()
            start = _try_parse_dt(a.findtext("Start") or a.findtext("StartDate"))
            finish = _try_parse_dt(a.findtext("Finish") or a.findtext("FinishDate"))

            if not aname and not aid:
                # سطر غير صالح
                continue

            # اسم المهمة
            name = f"{aid} - {aname}" if (aid and self.prefix_code_in_name) else (aname or aid)

            # هل لدينا مهمة بنفس الاسم داخل هذا المشروع؟
            existing = ProjectTask.search([("project_id", "=", self.project_id.id), ("name", "=", name)], limit=1)
            vals = {
                "name": name,
                "project_id": self.project_id.id,
            }
            # ملء تواريخ إن وُجدت حقول
            if "date_deadline" in ProjectTask._fields and finish:
                vals["date_deadline"] = fields.Datetime.to_string(finish)
            if "planned_date_begin" in ProjectTask._fields and start:
                vals["planned_date_begin"] = fields.Datetime.to_string(start)

            if existing:
                existing.write(vals)
                task = existing
                updated += 1
            else:
                task = ProjectTask.create(vals)
                created += 1

            if aid:
                id_to_task[aid] = task

        # استيراد العلاقات (اختياري)
        link_count = 0
        if self.import_relationships and has_pred_field and rels:
            for r in rels:
                pred = (r.findtext("PredecessorActivityId") or r.findtext("PredecessorId") or "").strip()
                succ = (r.findtext("SuccessorActivityId") or r.findtext("SuccessorId") or "").strip()
                # النوع (FS/SS/FF/SF) وLag يمكن تخزينهما في نموذج مخصص لاحقًا
                # rtype = (r.findtext("Type") or "").strip()
                # rlag = (r.findtext("Lag") or "0").strip()

                if pred in id_to_task and succ in id_to_task:
                    succ_task = id_to_task[succ]
                    # field name قد يختلف حسب تنفيذك؛ نتأكد من وجوده قبل الكتابة
                    try:
                        # نفترض M2M: predecessor_ids
                        succ_task.write({"predecessor_ids": [(4, id_to_task[pred].id)]})
                        link_count += 1
                    except Exception as e:
                        _logger.warning("تعذّر ربط علاقة للـ task %s → %s: %s", pred, succ, e)

        # إشعار بالنتيجة
        msg = _("تم استيراد مهام من P6\nأنشئ: %(c)s | حُدِّث: %(u)s\nعلاقات: %(l)s") % {
            "c": created, "u": updated, "l": link_count
        }
        # منشور على مشروعك
        self.project_id.message_post(body=msg)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("P6 Import"), "message": msg, "type": "success"},
        }
