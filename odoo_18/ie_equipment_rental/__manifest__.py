# -*- coding: utf-8 -*-
{
    'name': "ie_equipment_rental",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Ibrahim Elmasry",
    'license': 'LGPL-3',
    'website': "https://www.germaniatek.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'reports/rental_report.xml',
        'views/equipment_views.xml',
        'views/rental_views.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

