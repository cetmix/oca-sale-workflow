# Copyright 2026 Cetmix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Line Discount Mode Switch",
    "summary": "Switch between percentage and fixed amount discount per sale order line.",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "category": "Sales",
    "author": "Cetmix, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "license": "AGPL-3",
    "depends": ["sale_fixed_discount"],
    "data": ["views/sale_order_views.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
