from typing import Any

from odoo import api, models

from ..models.sale_order import SKIP_SYNC_CONTEXT_KEY

SYNC_TRIGGER_FIELDS = frozenset(
    {
        "discount",
        "discount_fixed",
        "product_id",
        "price_unit",
        "product_uom_qty",
        "display_type",
        "is_delivery",
        "is_downpayment",
    }
)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _sync_order_general_discount_fixed(self):
        """Resync and validate order-level fixed discount for affected orders."""
        orders = self.mapped("order_id").filtered("general_discount_fixed")
        if not orders:
            return

        orders = orders.with_context(**{SKIP_SYNC_CONTEXT_KEY: True})
        orders._sync_general_discount_fixed()
        orders._check_general_discount_fixed()

    @api.model_create_multi
    def create(self, vals_list: list[dict[str, Any]]) -> models.Model:
        """Create sale order lines and resync fixed discounts if needed."""
        lines = super().create(vals_list)
        lines._sync_order_general_discount_fixed()
        return lines

    def write(self, vals: dict[str, Any]) -> bool:
        """Write sale order line values and resync fixed discounts if needed."""
        result = super().write(vals)
        if self.env.context.get(SKIP_SYNC_CONTEXT_KEY):
            return result

        if SYNC_TRIGGER_FIELDS.intersection(vals):
            self._sync_order_general_discount_fixed()
        return result

    def unlink(self) -> bool:
        """Delete sale order lines and resync fixed discounts on remaining lines."""
        orders = self.mapped("order_id").filtered("general_discount_fixed")
        result = super().unlink()
        if orders and not self.env.context.get(SKIP_SYNC_CONTEXT_KEY):
            orders = orders.with_context(**{SKIP_SYNC_CONTEXT_KEY: True})
            orders._sync_general_discount_fixed()
            orders._check_general_discount_fixed()
        return result
