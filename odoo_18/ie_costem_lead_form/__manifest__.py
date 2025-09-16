# -*- coding: utf-8 -*-
{
    'name': "ie_costem_lead_form",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Ibrahim Elmasry",
    'website': "https://www.woledge.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/form_site_visit_view.xml',
        'views/check_box_fields_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

