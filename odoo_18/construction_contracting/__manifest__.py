# -*- coding: utf-8 -*-
{
    "name": "Construction Contracting",
    "summary": "BOQ → Project/Contract → Consultant Approval → IPC → Invoicing (Odoo 18)",
    "version": "18.0.1.0.0",
    "category": "Project/Construction",
    "author": "Ibrahim Elmasry",
    "website": "https://woledge.com",
    "license": "OEEL-1",

    # Dependencies
    "depends": [
        "base", "mail",
        "sale", "project", "purchase", "stock",
        "analytic",            # ضروري للـ Analytic Accounts / Lines
        "account", "hr_timesheet",
        "maintenance", "documents",
        "approvals",           # دورة موافقات
        "planning",            # لتخطيط الموارد
        # "base_automation",    # اختياري لو هتستخدم Automation Rules
    ],

    # Data Files
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/menus.xml",
        "views/estimate_views.xml",
        "views/contract_views.xml",
        "views/poq_view.xml",
        "views/equipment_view.xml",
        "views/ipc_views.xml",
        "views/res_config_settings_views.xml",
        "report/ipc_report.xml",
        "views/integration_wizard_views.xml",
        "views/report_evm_views.xml",
        "views/report_production_views.xml",
        "views/report_availability_views.xml",
        "views/report_equipment_views.xml",
        "views/report_cost_control_views.xml",
        "views/planning_views.xml",             # جديد (زر/تكامل Planning)
        "views/production_log_views.xml",       # جديد (Daily Production)
        "views/integration_wizard_views.xml",   # جديد (MSP/P6/IFC Import)
        "data/cron_shortage.xml",               # تنبيه نقص مخزون
        # "data/automated_actions.xml",         # فعّل عند الحاجة
    ],

    # Assets
    "assets": {
        "web.assets_backend": [
            # حط ملفات OWL/JS هنا عند الحاجة
        ]
    },

    "application": True,
    "installable": True,
}
