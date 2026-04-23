# Copyright 2026 Cetmix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Set discount mode to *fixed* on lines that already carry a fixed discount."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    lines = env["sale.order.line"].search(
        [
            "|",
            ("discount_fixed", ">", 0),
            ("discount_fixed", "<", 0),
        ]
    )
    if lines:
        lines.write({"discount_mode": "fixed"})
