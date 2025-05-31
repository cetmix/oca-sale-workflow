# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    DELAY_TYPE_SELECTION = [
        ("hours", "Hours"),
        ("days", "Days"),
    ]

    min_delivery_delay_type = fields.Selection(
        DELAY_TYPE_SELECTION,
        string="Minimum Delivery Delay Type",
        default="days",
        help="How to interpret the minimum delivery delay",
    )
    min_delivery_delay = fields.Float(
        string="Minimum Delivery Delay",
        default=1.0,
        help="Minimum delay between order placement and delivery",
    )
    weekday_rule_ids = fields.One2many(
        "delivery.weekday.rule",
        "carrier_id",
        string="Delivery Weekday Rules",
    )

    @api.constrains("min_delivery_delay")
    def _check_min_delivery_delay(self):
        for record in self:
            if record.min_delivery_delay < 0:
                raise ValidationError(_("Minimum delivery delay cannot be negative"))
