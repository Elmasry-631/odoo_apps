# -*- coding: utf-8 -*-
# Part of MultiBridges. See LICENSE file for full copyright and licensing details.
{
    'name': 'Print Journal Entries Report',
    'version': '18.0.0.0',
    'category': 'Accounting',
    'license': 'OPL-1',
    'summary': 'Professional PDF reports for journal entries with comprehensive details and calculations',
    'description': """
    Print Journal Entries Report
    ===========================
    
    Generate professional PDF reports for your journal entries with comprehensive details and calculations.
    
    Key Features:
    ------------
    * Print individual journal entry reports
    * Batch printing for multiple journal entries
    * Professional PDF layout with complete entry details
    * Automatic calculations for debit and credit totals
    * Clean and organized report format
    
    This module enables you to:
    --------------------------
    * Generate PDF reports directly from journal entries
    * Print multiple journal entries at once
    * View complete entry details in an organized layout
    * Access reports easily from the journal entry form
    """,
    'price': 000,
    'currency': 'EUR',
    'author': 'MultiBridges',
    'website': 'https://www.multibridges.com.sa',
    'depends': ['base', 'account'],
    'data': [
        'report/report_journal_entries.xml',
        'report/report_journal_entries_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': ['static/description/icon.png'],
    'maintainer': 'MultiBridges',
    'support': 'info@multibridges.com.sa',
}
