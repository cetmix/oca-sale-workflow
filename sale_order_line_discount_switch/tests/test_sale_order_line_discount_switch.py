# Copyright 2026 Cetmix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestSaleOrderLineDiscountSwitch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref("product.group_discount_per_so_line")
        cls.partner = cls.env["res.partner"].create({"name": "Partner DSwitch"})
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 15.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Product DSwitch", "type": "consu"}
        )

    def setUp(self):
        super().setUp()
        self.sale = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale.id,
                "name": "Line 1",
                "price_unit": 200.0,
                "product_uom_qty": 1,
                "product_id": self.product.id,
                "tax_id": [(6, 0, [self.tax.id])],
            }
        )

    def test_01_percent_mode_standard_discount(self):
        self.assertEqual(self.line.discount_mode, "percent")
        self.assertEqual(self.line.discount_fixed, 0.0)
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount = 10.0
        self.assertEqual(self.sale.order_line[0].price_subtotal, 180.0)
        self.assertEqual(self.sale.order_line[0].discount_fixed, 0.0)

    def test_02_fixed_mode_matches_sale_fixed_discount(self):
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount_mode = "fixed"
                line.discount_fixed = 20.0
        line = self.sale.order_line[0]
        self.assertEqual(line.discount, 10.0)
        self.assertEqual(line.price_subtotal, 180.0)

    def test_03_switch_percent_clears_fixed_keeps_percent_discount(self):
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount_mode = "fixed"
                line.discount_fixed = 20.0
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount_mode = "percent"
        line = self.sale.order_line[0]
        self.assertEqual(line.discount_fixed, 0.0)
        self.assertEqual(line.discount, 10.0)

    def test_04_cannot_set_fixed_in_percent_mode(self):
        self.line.write({"discount": 0.0, "discount_fixed": 0.0})
        with self.assertRaises(ValidationError):
            self.line.write({"discount_fixed": 15.0})

    def test_05_switch_to_fixed_converts_from_percent(self):
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount = 10.0
        with Form(self.sale) as order:
            with order.order_line.edit(0) as line:
                line.discount_mode = "fixed"
        line = self.sale.order_line[0]
        self.assertEqual(line.discount_fixed, 20.0)
        self.assertEqual(line.discount, 10.0)

    def test_06_write_switch_to_fixed_fills_from_percent(self):
        self.line.write({"discount": 10.0})
        self.line.write({"discount_mode": "fixed"})
        self.assertEqual(self.line.discount_fixed, 20.0)
        self.assertEqual(self.line.discount, 10.0)

    def test_07_write_switch_to_fixed_respects_explicit_fixed(self):
        self.line.write({"discount": 10.0})
        self.line.write(
            {"discount_mode": "fixed", "discount_fixed": 50.0, "discount": 25.0}
        )
        self.assertEqual(self.line.discount_fixed, 50.0)
        self.assertEqual(self.line.discount, 25.0)
