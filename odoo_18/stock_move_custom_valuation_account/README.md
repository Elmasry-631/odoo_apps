# Stock Move Custom Valuation Account

This module adds a per-picking and per-move "Valuation Account" override. If defined, the account is used for stock valuation journal entries, bypassing the product category default accounts.

## Notes & Compatibility
- Tested paths for Odoo 16/17 where `stock_account` uses `_get_accounting_data_for_valuation()`.
- If your fork overrides valuation differently, adapt the hook in `stock_move.py` accordingly (e.g., `_create_account_move_line`).

## Installation
1. Drop the folder `stock_move_custom_valuation_account` into your addons path.
2. Update Apps list and install.

## Usage
- On a Picking: set **Valuation Account (Override)** -> all moves take it by default.
- On a Move: set **Valuation Account (Override)** -> only that move uses it.

## Advanced: Split by Direction
If you need different accounts for incoming vs outgoing, extend the model with two fields and set `res['account_src']` vs `res['account_dest']` accordingly.
