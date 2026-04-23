# Copyright 2026 Cetmix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_mode = fields.Selection(
        selection=[
            ("percent", "Percentage"),
            ("fixed", "Fixed amount"),
        ],
        string="Discount type",
        default="percent",
        required=True,
        help="Percentage: standard discount on the line. Fixed amount: use the fixed "
        "discount field (see sale fixed discount).",
    )

    @api.constrains("discount_mode", "discount_fixed")
    def _check_discount_mode_fixed_clear(self):
        prec = self.env["decimal.precision"].precision_get("Product Price")
        rounding = 10**-prec if prec else 0.0001
        for line in self:
            if line.discount_mode != "percent":
                continue
            if float_is_zero(line.discount_fixed, precision_rounding=rounding):
                continue
            raise ValidationError(
                _(
                    "In percentage discount mode, the fixed discount must be zero "
                    "on line %(line)s."
                )
                % {"line": line.name or str(line.id)}
            )

    @api.onchange("discount_mode")
    def _onchange_discount_mode(self):
        if self.discount_mode == "percent":
            self.discount_fixed = 0.0
            return
        if self.discount_mode == "fixed":
            if self.price_unit:
                prec = self.env["decimal.precision"].precision_get("Product Price")
                self.discount_fixed = float_round(
                    (self.price_unit * self.discount) / 100.0,
                    precision_digits=prec,
                )
            else:
                self.discount_fixed = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        clean_vals = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get("discount_mode", "percent") == "percent":
                vals.setdefault("discount_fixed", 0.0)
            clean_vals.append(vals)
        return super().create(clean_vals)

    def write(self, vals):
        vals = dict(vals)
        if vals.get("discount_mode") == "percent":
            vals["discount_fixed"] = 0.0
        will_convert_percent_to_fixed = bool(
            vals.get("discount_mode") == "fixed" and "discount_fixed" not in vals
        )
        lines_to_fill_fixed = self.env["sale.order.line"]
        if will_convert_percent_to_fixed:
            lines_to_fill_fixed = self.filtered(
                lambda line: line.discount_mode == "percent"
            )
        res = super().write(vals)
        for line in lines_to_fill_fixed:
            if not line.discount_mode == "fixed":
                continue
            if float_is_zero(
                line.price_unit, precision_rounding=1e-10
            ) or float_is_zero(line.discount, precision_rounding=1e-10):
                continue
            prec = self.env["decimal.precision"].precision_get("Product Price")
            fixed = float_round(
                (line.price_unit * line.discount) / 100.0,
                precision_digits=prec,
            )
            if float_compare(line.discount_fixed, fixed, precision_digits=prec) == 0:
                continue
            line.write({"discount_fixed": fixed})
        return res
