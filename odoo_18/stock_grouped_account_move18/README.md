# Stock Grouped Account Move (Odoo 18)

**Goal:** In Odoo 18, when a stock picking has multiple products, create one journal entry (`account.move`) containing multiple lines (one per product), instead of a separate journal entry per product.

## How it works
This module overrides the valuation entry creation in `stock_account` to reuse a single draft `account.move` per `(picking, journal, company)`.

## Install
1. Copy this folder to your Odoo 18 addons path.
2. Update apps list and install **Stock Grouped Account Move (v18)**.
3. Ensure Inventory Valuation is Automated.

## Notes
- Targeted for Odoo 18.
- The `ref` of the move equals the picking name.
- Lines still detailed per product.