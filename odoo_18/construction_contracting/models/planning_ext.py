# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectTask(models.Model):
    _inherit = "project.task"

    def action_create_planning_slot(self):
        """ينشئ planning.slot بسيط مرتبط بالمهمة (اختياري)."""
        Planning = self.env["planning.slot"]
        for t in self:
            # لو التواريخ غير معرّفة، تجاهل بهدوء
            start = t.date_deadline or t.create_date
            end = t.date_deadline or t.create_date
            if not start or not end:
                continue
            Planning.create({
                "name": t.name,
                "project_id": t.project_id.id,
                "task_id": t.id,
                # resource_type: موظف/معدّة — يُحدَّد عند الاستخدام
                # employee_id أو resource_id حسب تكوينك
                "start_datetime": start,
                "end_datetime": end,
            })
        return True
