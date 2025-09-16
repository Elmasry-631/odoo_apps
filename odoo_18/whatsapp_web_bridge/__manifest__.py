{
    "name": "WhatsApp Web Bridge (No API)",
    "version": "18.0.1.0.0",
    "summary": "Send messages to WhatsApp Web from Odoo without any API",
    "author": "GermaniaTek",
    "website": "https://www.germaniatek.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "contacts", "account", "sale_management", "stock", "project"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/whatsapp_log_views.xml",
        "views/partner_views.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "views/project_task_views.xml",
        "wizards/whatsapp_compose_views.xml"
    ],
    "assets": {},
    "installable": True,
    "application": False
}