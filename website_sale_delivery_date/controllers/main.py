# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDeliveryDate(WebsiteSale):
    @http.route(["/shop/checkout"], type="http", auth="public", website=True)
    def checkout(self, **post):
        res = super().checkout(**post)
        if request.httprequest.method == "POST":
            delivery_date = post.get("delivery_date")
            if delivery_date:
                try:
                    delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d")
                    order = request.website.sale_get_order()
                    if order and order.carrier_id:
                        self._validate_delivery_date(order, delivery_date)
                        order.commitment_date = delivery_date
                except ValueError:
                    return request.redirect("/shop/checkout?error=invalid_date")
                except ValidationError as e:
                    return request.redirect(f"/shop/checkout?error={str(e)}")
        return res

    @http.route(
        ["/shop/delivery_date_constraints"], type="json", auth="public", website=True
    )
    def delivery_date_constraints(self, carrier_id=None, **kw):
        """Get delivery date constraints for the selected carrier."""
        if not carrier_id:
            return False

        carrier = request.env["delivery.carrier"].sudo().browse(int(carrier_id))
        if not carrier.exists():
            return False

        now = datetime.now()

        # Calculate minimum delivery date
        if carrier.min_delivery_delay_type == "hours":
            min_date = now + timedelta(hours=carrier.min_delivery_delay)
        else:  # days
            min_date = now + timedelta(days=carrier.min_delivery_delay)
            min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate maximum delivery date (e.g., 30 days from now)
        max_date = now + timedelta(days=30)

        return {
            "min_date": min_date.strftime("%Y-%m-%d"),
            "max_date": max_date.strftime("%Y-%m-%d"),
        }

    @http.route(
        ["/shop/validate_delivery_date"], type="json", auth="public", website=True
    )
    def validate_delivery_date(self, delivery_date=None, carrier_id=None, **kw):
        """Validate the selected delivery date."""
        if not delivery_date or not carrier_id:
            return {"valid": False, "message": "Invalid input"}

        try:
            delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d")
            carrier = request.env["delivery.carrier"].sudo().browse(int(carrier_id))

            if not carrier.exists():
                return {"valid": False, "message": "Invalid carrier"}

            self._validate_delivery_date(
                request.website.sale_get_order(), delivery_date
            )
            return {"valid": True}
        except ValidationError as e:
            return {"valid": False, "message": str(e)}
        except Exception:
            return {"valid": False, "message": "Invalid date format"}

    def _validate_delivery_date(self, order, delivery_date):
        """Validate the delivery date against carrier constraints."""
        carrier = order.carrier_id
        if not carrier:
            return True

        # Get current time
        now = datetime.now()

        # Calculate minimum delivery time based on delay type
        if carrier.min_delivery_delay_type == "hours":
            min_delivery_time = now + timedelta(hours=carrier.min_delivery_delay)
        else:  # days
            min_delivery_time = now + timedelta(days=carrier.min_delivery_delay)
            # Set to start of day
            min_delivery_time = min_delivery_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        # Check if delivery date is after minimum delivery time
        if delivery_date < min_delivery_time:
            raise ValidationError(
                _("Selected delivery date is before the minimum delivery time")
            )

        # Get weekday rule for the delivery date
        weekday = delivery_date.strftime("%A").lower()
        weekday_rule = carrier.weekday_rule_ids.filtered(
            lambda r: r.weekday == weekday and r.active
        )

        if not weekday_rule:
            raise ValidationError(
                _("Delivery is not available on %(weekday)s", weekday=weekday)
            )

        # Check delivery hours
        delivery_hour = delivery_date.hour + delivery_date.minute / 60
        if not (
            weekday_rule.delivery_start_hour
            <= delivery_hour
            <= weekday_rule.delivery_end_hour
        ):
            raise ValidationError(
                _(
                    "Delivery time must be between "
                    "%(start_hour)s:00 and "
                    "%(end_hour)s:00",
                    start_hour=weekday_rule.delivery_start_hour,
                    end_hour=weekday_rule.delivery_end_hour,
                )
            )

        # Check cut-off time if defined
        if weekday_rule.cutoff_hour:
            cutoff_time = now.replace(
                hour=int(weekday_rule.cutoff_hour),
                minute=int((weekday_rule.cutoff_hour % 1) * 60),
                second=0,
                microsecond=0,
            )
            if now > cutoff_time:
                raise ValidationError(
                    _(
                        "Order placed after cut-off time " "%(cutoff_hour)s:00",
                        cutoff_hour=weekday_rule.cutoff_hour,
                    )
                )

        return True
