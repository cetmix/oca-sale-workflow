# Copyright (C) 2026 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase
from odoo.tools.float_utils import float_compare


class TestSaleOrderGeneralDiscountFixed(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})

        cls.partner = cls.env["res.partner"].create(
            {"name": "General Fixed Discount Customer"}
        )

        cls.product_0 = cls.env["product.product"].create(
            {
                "name": "Product 0",
                "list_price": 0.0,
                "type": "consu",
                "taxes_id": [(6, 0, [])],
            }
        )
        cls.product_100 = cls.env["product.product"].create(
            {
                "name": "Product 100",
                "list_price": 100.0,
                "type": "consu",
                "taxes_id": [(6, 0, [])],
            }
        )
        cls.product_300 = cls.env["product.product"].create(
            {
                "name": "Product 300",
                "list_price": 300.0,
                "type": "consu",
                "taxes_id": [(6, 0, [])],
            }
        )

    def test_single_line_full_discount_assigned(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        form.general_discount_fixed = 10.0
        order = form.save()

        line = order.order_line.filtered(lambda ln: not ln.display_type)
        self.assertEqual(len(line), 1)
        self.assertEqual(
            float_compare(
                line.discount_fixed,
                10.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                order.amount_untaxed,
                90.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

    def test_multi_line_split_sums_exactly_to_global_discount(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        with form.order_line.new() as line:
            line.product_id = self.product_300
            line.product_uom_qty = 1
        form.general_discount_fixed = 40.0
        order = form.save()

        lines = order.order_line.filtered(lambda ln: not ln.display_type).sorted(
            key=lambda l: l.price_unit
        )

        self.assertEqual(
            float_compare(
                lines[0].discount_fixed,
                10.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                lines[1].discount_fixed,
                30.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

        gross_amount = sum(
            line.price_unit * line.product_uom_qty
            for line in order.order_line.filtered(lambda l: not l.display_type)
        )
        effective_discount = gross_amount - order.amount_untaxed

        self.assertEqual(
            float_compare(
                effective_discount,
                40.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                order.amount_untaxed,
                360.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

    def test_zero_price_line_gets_zero_discount(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        with form.order_line.new() as line:
            line.product_id = self.product_0
            line.product_uom_qty = 1
        form.general_discount_fixed = 20.0
        order = form.save()

        paid_line = order.order_line.filtered(
            lambda l: not l.display_type and l.price_unit > 0
        )
        free_line = order.order_line.filtered(
            lambda l: not l.display_type and l.price_unit == 0
        )

        self.assertEqual(
            float_compare(
                paid_line.discount_fixed,
                20.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                free_line.discount_fixed,
                0.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                order.amount_untaxed,
                80.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

    def test_rounding_on_three_equal_lines(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        form.general_discount_fixed = 10.0
        order = form.save()

        discounts = sorted(
            order.order_line.filtered(lambda l: not l.display_type).mapped(
                "discount_fixed"
            )
        )

        self.assertEqual(
            float_compare(
                discounts[0],
                3.33,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                discounts[1],
                3.33,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                discounts[2],
                3.34,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

        gross_amount = sum(
            line.price_unit * line.product_uom_qty
            for line in order.order_line.filtered(lambda l: not l.display_type)
        )
        effective_discount = gross_amount - order.amount_untaxed

        self.assertEqual(
            float_compare(
                effective_discount,
                10.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                order.amount_untaxed,
                290.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

    def test_remove_line_and_retrigger_distribution(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product_100
            line.product_uom_qty = 1
        with form.order_line.new() as line:
            line.product_id = self.product_300
            line.product_uom_qty = 1
        form.general_discount_fixed = 40.0
        order = form.save()

        line_to_remove = order.order_line.filtered(
            lambda l: not l.display_type and l.price_unit == 100.0
        )
        line_to_remove.unlink()

        order.invalidate_recordset(["amount_untaxed", "amount_total"])
        remaining_line = order.order_line.filtered(lambda ln: not ln.display_type)

        self.assertEqual(len(remaining_line), 1)
        self.assertEqual(
            float_compare(
                remaining_line.discount_fixed,
                40.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                order.amount_untaxed,
                260.0,
                precision_rounding=order.currency_id.rounding,
            ),
            0,
        )

    def test_discount_cannot_exceed_order_amount(self):
        with self.assertRaises(ValidationError):
            form = Form(self.env["sale.order"])
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.product_100
                line.product_uom_qty = 1
            form.general_discount_fixed = 150.0
            form.save()
