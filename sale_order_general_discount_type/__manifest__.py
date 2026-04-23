# Copyright (C) 2026 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order General Discount Type",
    "summary": "Adds a Discount Type selector on Sale Orders",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Cetmix, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sales",
    "depends": [
        "sale_order_general_discount",
        "sale_order_general_discount_fixed",
    ],
    "data": [
        "views/sale_order_views.xml",
    ],
}
