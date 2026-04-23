# Copyright (C) 2026 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Any

from odoo import api, fields, models

SKIP_DISCOUNT_TYPE_CLEANUP_CONTEXT_KEY = "skip_discount_type_cleanup"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _selection_general_discount_type(self) -> list[tuple[str, str]]:
        """Return available general discount types.

        :return: Available discount type options.
        """
        return [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ]

    @api.model
    def _default_general_discount_type(self) -> str:
        """Return default general discount type.

        :return: Default discount type code.
        """
        return "percent"

    general_discount_type = fields.Selection(
        selection="_selection_general_discount_type",
        string="Discount Type",
        default=lambda self: self._default_general_discount_type(),
        required=True,
    )

    def _get_hidden_discount_cleanup_vals(self) -> dict[str, float]:
        """Return values needed to clear the hidden discount field.

        :return: Values for the non-selected discount field.
        """
        self.ensure_one()
        if self.general_discount_type == "fixed":
            return {"general_discount": 0.0}
        return {"general_discount_fixed": 0.0}

    def _cleanup_hidden_discount_field(self, use_write: bool = True):
        """Clear the discount field hidden by the selected discount type.

        :param use_write: Whether to persist values with ``write``.
        """
        for order in self:
            vals = order._get_hidden_discount_cleanup_vals()
            field_name, field_value = next(iter(vals.items()))
            if order[field_name] == field_value:
                continue
            if use_write:
                order.with_context(
                    **{SKIP_DISCOUNT_TYPE_CLEANUP_CONTEXT_KEY: True}
                ).write(vals)
            else:
                order.update(vals)

    @api.model_create_multi
    def create(self, vals_list: list[dict[str, Any]]) -> models.Model:
        """Create sale orders and clear the hidden discount field.

        :param vals_list: Values for created sale orders.
        :return: Created sale orders.
        """
        orders = super().create(vals_list)
        orders._cleanup_hidden_discount_field()
        return orders

    def write(self, vals: dict[str, Any]) -> bool:
        """Write sale order values and clear hidden discount fields when needed.

        :param vals: Values to write on the order.
        :return: Result of parent ``write``.
        """
        result = super().write(vals)
        if self.env.context.get(SKIP_DISCOUNT_TYPE_CLEANUP_CONTEXT_KEY):
            return result
        if {"general_discount_type", "partner_id"}.intersection(vals):
            self._cleanup_hidden_discount_field()
        return result

    @api.onchange("general_discount_type")
    def _onchange_general_discount_type(self):
        """Clear the hidden discount field when the type changes."""
        self._cleanup_hidden_discount_field(use_write=False)

    @api.onchange("partner_id")
    def _onchange_partner_id_discount_type(self):
        """Prevent hidden partner default percentage from remaining on fixed mode."""
        if self.general_discount_type == "fixed":
            self._cleanup_hidden_discount_field(use_write=False)
