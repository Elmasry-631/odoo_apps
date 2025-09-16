# stock_movement_report/__manifest__.py
{
    "name": "Stock Movement Detailed Report",
    "version": "2.0.0",
    "sequence": -100,
    "summary": "Detailed In/Out/Balance stock movements report (PDF)",
    "description": """
            Generate detailed stock movement reports (In/Out/Balance) 
            for single or multiple products within a date range, 
            with optional category filtering.
        """,
    "category": "Inventory/Reporting",
    "author": "Ibrahim Elmasry",
    "website": "https://www.woledge.com",
    "depends": [
        "stock",
        "product",
        "ie_mtno",
    ],
    "data": [
        "report/stock_movement_report_templates.xml",
        "security/ir.model.access.csv",
        "views/stock_movement_report_wizard_view.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
