# Copyright (C) 2026 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Any

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

SKIP_SYNC_CONTEXT_KEY = "skip_general_discount_fixed_sync"
DEFAULT_ROUNDING = 0.01
ZERO_DISCOUNT_VALUES = {"discount_fixed": 0.0, "discount": 0.0}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    general_discount_fixed = fields.Monetary(
        string="General Fixed Discount",
        currency_field="currency_id",
        help=(
            "Fixed amount discount in the sales order currency. "
            "The amount is distributed proportionally across commercial order lines."
        ),
    )

    def _get_general_discount_fixed_rounding(self) -> float:
        """Return safe currency rounding for fixed-discount computations.

        :return: Positive rounding precision.
        """
        self.ensure_one()
        rounding = (
            self.currency_id.rounding
            or self.company_id.currency_id.rounding
            or self.env.company.currency_id.rounding
            or DEFAULT_ROUNDING
        )
        return rounding if rounding > 0 else DEFAULT_ROUNDING

    def _get_general_discount_fixed_commercial_lines(self) -> models.Model:
        """Return commercial order lines eligible for reset logic.

        :return: Non-display order lines.
        """
        self.ensure_one()
        return self.order_line.filtered(lambda line: not line.display_type)

    def _get_general_discount_fixed_discountable_lines(
        self,
        commercial_lines: models.Model | None = None,
    ) -> models.Model:
        """Return order lines that can receive a fixed discount allocation.

        :param commercial_lines: Optional prefiltered commercial lines.
        :return: Lines allowed to receive fixed discount.
        """
        self.ensure_one()
        lines = commercial_lines or self._get_general_discount_fixed_commercial_lines()
        return lines.filtered(
            lambda line: line.product_uom_qty > 0
            and line.price_unit > 0
            and not getattr(line, "is_delivery", False)
            and not getattr(line, "is_downpayment", False)
        )

    def _get_general_discount_fixed_base_amount(
        self,
        lines: models.Model | None = None,
    ) -> float:
        """Return the allocation base amount for the fixed discount.

        :param lines: Optional line set to use as allocation base.
        :return: Base amount used for proportional split.
        """
        self.ensure_one()
        lines = lines or self._get_general_discount_fixed_discountable_lines()
        return sum(line.price_unit * line.product_uom_qty for line in lines)

    def _get_general_discount_fixed_fallback_discount(self) -> float:
        """Return percentage fallback discount when fixed discount is reset.

        If ``sale_order_general_discount`` is installed, its order-level discount
        is restored on lines after clearing the fixed discount.

        :return: Fallback percentage discount.
        """
        self.ensure_one()
        return self.general_discount if "general_discount" in self._fields else 0.0

    def _apply_general_discount_fixed_values(
        self,
        lines: models.Model,
        values: dict[str, float],
        use_write: bool = True,
    ):
        """Apply computed fixed-discount values to order lines.

        :param lines: Target order lines.
        :param values: Values to apply on each line.
        :param use_write: Whether to persist values with ``write``.
        """
        if not lines:
            return

        if use_write:
            lines.with_context(**{SKIP_SYNC_CONTEXT_KEY: True}).write(values)
        else:
            lines.update(values)

    def _get_general_discount_fixed_line_values(
        self,
        line: models.Model,
        line_discount: float,
    ) -> tuple[float, dict[str, float]]:
        """Prepare line values for a proportional fixed-discount share.

        :param line: Sale order line to update.
        :param line_discount: Total fixed discount allocated to the line.
        :return: Tuple of actual applied line discount and write values.
        """
        self.ensure_one()

        per_unit_discount = line._fields["discount_fixed"].convert_to_cache(
            line_discount / line.product_uom_qty,
            line,
        )
        actual_line_discount = self.currency_id.round(
            per_unit_discount * line.product_uom_qty
        )
        values = {
            "discount_fixed": per_unit_discount,
            "discount": (per_unit_discount / line.price_unit) * 100,
        }
        return actual_line_discount, values

    @api.onchange("general_discount_fixed")
    def _onchange_general_discount_fixed(self):
        """Recompute line discounts during form onchange."""
        if self.env.context.get(SKIP_SYNC_CONTEXT_KEY):
            return
        self._sync_general_discount_fixed(use_write=False)

    def write(self, vals: dict[str, Any]) -> bool:
        """Write order values and resync fixed discount when needed.

        :param vals: Values to write on the order.
        :return: Result of parent ``write``.
        """
        result = super().write(vals)
        if (
            not self.env.context.get(SKIP_SYNC_CONTEXT_KEY)
            and "general_discount_fixed" in vals
        ):
            self._sync_general_discount_fixed()
        return result

    @api.constrains("general_discount_fixed", "order_line")
    def _check_general_discount_fixed(self):
        """Validate order-level fixed discount constraints.

        :raise ValidationError: If the fixed discount is invalid.
        """
        for order in self:
            rounding = order._get_general_discount_fixed_rounding()
            discount = order.general_discount_fixed or 0.0

            if float_compare(discount, 0.0, precision_rounding=rounding) < 0:
                raise ValidationError(_("The general fixed discount must be positive."))

            if float_compare(discount, 0.0, precision_rounding=rounding) == 0:
                continue

            base_amount = order._get_general_discount_fixed_base_amount()
            if float_compare(base_amount, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError(
                    _(
                        "A positive commercial amount is required before applying "
                        "a general fixed discount."
                    )
                )

            if (
                float_compare(
                    discount,
                    base_amount,
                    precision_rounding=rounding,
                )
                > 0
            ):
                raise ValidationError(
                    _(
                        "The general fixed discount cannot exceed the commercial "
                        "amount of the sales order."
                    )
                )

    def _sync_general_discount_fixed(self, use_write: bool = True):
        """Distribute the order fixed discount across eligible order lines.

        :param use_write: Whether to persist values with ``write`` instead of
            ``update``.
        """
        for order in self:
            commercial_lines = order._get_general_discount_fixed_commercial_lines()
            if not commercial_lines:
                continue

            rounding = order._get_general_discount_fixed_rounding()
            discount = order.general_discount_fixed or 0.0

            if float_compare(discount, 0.0, precision_rounding=rounding) <= 0:
                order._apply_general_discount_fixed_values(
                    commercial_lines,
                    {
                        "discount_fixed": 0.0,
                        "discount": order._get_general_discount_fixed_fallback_discount(),
                    },
                    use_write=use_write,
                )
                continue

            discountable_lines = order._get_general_discount_fixed_discountable_lines(
                commercial_lines
            )
            base_amount = order._get_general_discount_fixed_base_amount(
                discountable_lines
            )
            if float_compare(base_amount, 0.0, precision_rounding=rounding) <= 0:
                continue

            excluded_lines = commercial_lines - discountable_lines
            order._apply_general_discount_fixed_values(
                excluded_lines,
                ZERO_DISCOUNT_VALUES,
                use_write=use_write,
            )

            remaining_discount = discount
            currency_round = order.currency_id.round
            last_index = len(discountable_lines) - 1

            for index, line in enumerate(discountable_lines):
                if index == last_index:
                    line_discount = remaining_discount
                else:
                    line_discount = currency_round(
                        discount
                        * ((line.price_unit * line.product_uom_qty) / base_amount)
                    )

                (
                    actual_line_discount,
                    values,
                ) = order._get_general_discount_fixed_line_values(
                    line,
                    line_discount,
                )
                remaining_discount -= actual_line_discount
                order._apply_general_discount_fixed_values(
                    line,
                    values,
                    use_write=use_write,
                )
