
{
    'name': 'Journal Entry Currency Split',
    'version': '1.0',
    'author': 'Ibrahim Elmasry',
    'category': 'Accounting',
    'summary': 'Show debit and credit in foreign currency on journal entries',
    'depends': ['account'],
    'data': [
        'views/account_move_line_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
