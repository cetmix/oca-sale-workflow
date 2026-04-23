# Copyright (C) 2026 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form, TransactionCase


class TestSaleOrderGeneralDiscountType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner with default discount",
                "sale_discount": 15.0,
            }
        )
        template = cls.env["product.template"].create(
            {
                "name": "Test product",
                "list_price": 100.0,
                "type": "consu",
                "taxes_id": [(6, 0, [])],
            }
        )
        cls.product = template.product_variant_id

    def _new_order_form(self):
        form = Form(self.env["sale.order"])
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1
        return form

    def test_discount_type_defaults_to_percent(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.assertEqual(order.general_discount_type, "percent")

    def test_onchange_switch_to_fixed_clears_percentage_value(self):
        form = self._new_order_form()
        self.assertEqual(form.general_discount, 15.0)
        form.general_discount_type = "fixed"
        form.general_discount_fixed = 20.0
        order = form.save()

        self.assertEqual(order.general_discount_type, "fixed")
        self.assertEqual(order.general_discount, 0.0)
        self.assertEqual(order.general_discount_fixed, 20.0)

    def test_onchange_switch_to_percent_clears_fixed_value(self):
        form = self._new_order_form()
        form.general_discount_type = "fixed"
        form.general_discount_fixed = 25.0
        form.general_discount_type = "percent"
        order = form.save()

        self.assertEqual(order.general_discount_type, "percent")
        self.assertEqual(order.general_discount_fixed, 0.0)

    def test_partner_change_keeps_hidden_percentage_cleared_for_fixed_type(self):
        form = self._new_order_form()
        form.general_discount_type = "fixed"
        form.general_discount_fixed = 30.0
        order = form.save()

        self.assertEqual(order.general_discount, 0.0)

        new_partner = self.env["res.partner"].create(
            {
                "name": "Another partner",
                "sale_discount": 20.0,
            }
        )
        order.write({"partner_id": new_partner.id})

        self.assertEqual(order.general_discount_type, "fixed")
        self.assertEqual(order.general_discount, 0.0)
        self.assertEqual(order.general_discount_fixed, 30.0)

    def test_view_contains_selector_and_visibility_rules(self):
        view = self.env["sale.order"].get_view(view_type="form")
        xml = etree.XML(view["arch"])

        self.assertTrue(xml.xpath("//field[@name='general_discount_type']"))

        percent_nodes = xml.xpath("//field[@name='general_discount']")
        fixed_nodes = xml.xpath("//field[@name='general_discount_fixed']")

        self.assertTrue(percent_nodes)
        self.assertTrue(fixed_nodes)

        percent_has_visibility_rule = any(
            "general_discount_type"
            in (
                node.attrib.get("attrs", "")
                + node.attrib.get("modifiers", "")
                + node.attrib.get("invisible", "")
            )
            for node in percent_nodes
        )
        fixed_has_visibility_rule = any(
            "general_discount_type"
            in (
                node.attrib.get("attrs", "")
                + node.attrib.get("modifiers", "")
                + node.attrib.get("invisible", "")
            )
            for node in fixed_nodes
        )

        self.assertTrue(percent_has_visibility_rule)
        self.assertTrue(fixed_has_visibility_rule)
