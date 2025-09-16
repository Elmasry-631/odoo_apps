{
    'name': 'IE Print Document Linked Order',
    'version': '0.1',
    'summary': 'Show all product attachments directly from Quotation.',
    'description': """
        This module adds a button in the Sale Order (Quotation) form
        to quickly view all attachments linked to the products
        in the quotation/order.
    """,
    'category': 'Sales',
    'author': 'Ibrahim Elmasry',
    'website': 'https://www.woledge.com',
    'license': 'LGPL-3',
    'depends': ['base', 'sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
