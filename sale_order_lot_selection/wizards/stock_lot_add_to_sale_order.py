# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class StockLotAddToSaleOrder(models.TransientModel):
    _name = "stock.lot.add.to.sale.order.wizard"
    _description = "Add Lot to Sale Order Wizard"

    line_ids = fields.One2many(
        "stock.lot.add.to.sale.order.wizard.line",
        "wizard_id",
        string="Lot Lines",
    )

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        domain="[('state', 'not in', ['done', 'cancel'])]",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        store=True,
        compute="_compute_partner_id",
    )

    @api.depends("sale_order_id")
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = record.sale_order_id.partner_id.id

    def open_wizard(self, lot_ids):
        """Open the wizard with selected lots."""
        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_order_lot_selection.allow_generate_from_lots")
        ):
            raise AccessError(_("You are not allowed to generate Sale Order from Lot."))
        vals = {
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "lot_id": lot_id.id,
                        "quantity": lot_id.product_qty,
                    },
                )
                for lot_id in lot_ids
            ]
        }
        wizard_id = self.create(vals)

        return {
            "type": "ir.actions.act_window",
            "name": "Add Lot to Sale Order",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": wizard_id.id,
            "target": "new",
        }

    def action_add_lots_to_sale_order(self):
        """Add selected lots to the existing sale order."""
        self.ensure_one()
        if not self.sale_order_id:
            raise ValidationError(_("Please select a Sale Order"))
        self.sale_order_id.write(
            {
                "order_line": self._get_vals_for_add_lot_in_sale_order_line(),
            }
        )
        return self._action_open_sale_order()

    def action_create_sale_order(self):
        """Create a sale order from the selected lots."""
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_("Please select a Customer"))
        self.sale_order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": self._get_vals_for_add_lot_in_sale_order_line(),
            }
        )
        return self._action_open_sale_order()

    def _get_vals_for_add_lot_in_sale_order_line(self):
        """Get values for adding lot in sale order line."""
        if not self.line_ids:
            raise ValidationError(_("Please select at least one lot"))
        return [
            (
                0,
                0,
                {
                    "lot_id": line_id.lot_id.id,
                    "product_id": line_id.lot_id.product_id.id,
                    "product_uom_qty": line_id.quantity,
                },
            )
            for line_id in self.line_ids
        ]

    def _action_open_sale_order(self):
        """Open the sale order form view."""
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Order",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.sale_order_id.id,
            "target": "current",
        }


class StockLotAddToSaleOrderLine(models.TransientModel):
    _name = "stock.lot.add.to.sale.order.wizard.line"
    _description = "Add Lot to Sale Order Wizard Line"

    wizard_id = fields.Many2one(
        "stock.lot.add.to.sale.order.wizard",
        string="Wizard",
        required=True,
    )
    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot",
        required=True,
    )
    product_id = fields.Many2one(related="lot_id.product_id")
    quantity = fields.Float(string="Quantity")  # pylint: disable=W8113
    max_qty = fields.Float(string="Max Quantity", related="lot_id.product_qty")

    @api.constrains("quantity")
    def _check_quantity(self):
        """Check that the quantity is not greater than the max quantity."""
        for record in self:
            if record.quantity > record.max_qty:
                raise ValidationError(
                    _(
                        "The quantity of lot %(lot_name)s cannot be greater than "
                        "the available quantity %(max_qty)s.",
                        lot_name=record.lot_id.name,
                        max_qty=record.max_qty,
                    )
                )


class StockLot(models.Model):
    _inherit = "stock.lot"

    def action_add_to_sale_order(self):
        """Open the wizard to add lots to a sale order."""
        self.ensure_one()
        return self.env["stock.lot.add.to.sale.order.wizard"].open_wizard(self)
