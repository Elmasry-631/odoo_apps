# -*- coding: utf-8 -*-
{
    'name': "account_enhancement",

    'summary': """
        Account Enhancement""",

    'description': """
        Account Enhancement
    """,

    'author': "Akram Refaat",
    'website': "WWW.SPL-PRO.COM",
    'category': 'Accounting',
    'version': '1.0',

    'depends': ['base','account','account_reports'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/account_payment_register.xml',
        'views/account_journal.xml',
        'views/account_account.xml',
        'data/server_action_adjust_journal.xml',
    ],

}