odoo.define("website_sale_delivery_date.delivery_date", [], function () {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.DeliveryDate = publicWidget.Widget.extend({
        selector: "#delivery_date_picker",
        events: {
            "change input[name='delivery_type']": "_onDeliveryTypeChange",
            "change #delivery_date": "_onDeliveryDateChange",
        },

        start: function () {
            var self = this;
            var $datePicker = this.$el;
            var $dateInput = $("#delivery_date");

            // Инициализация datepicker
            if (typeof $.fn.datetimepicker !== "undefined") {
                $datePicker.datetimepicker({
                    format: "YYYY-MM-DD HH:mm",
                    minDate: new Date(),
                    stepping: 30,
                    icons: {
                        time: "fa fa-clock-o",
                        date: "fa fa-calendar",
                        up: "fa fa-chevron-up",
                        down: "fa fa-chevron-down",
                        previous: "fa fa-chevron-left",
                        next: "fa fa-chevron-right",
                        today: "fa fa-screenshot",
                        clear: "fa fa-trash",
                        close: "fa fa-remove",
                    },
                });
            }
            return this._super.apply(this, arguments);
        },

        _onDeliveryTypeChange: function (ev) {
            var self = this;
            var carrierId = $(ev.currentTarget).val();
            var $datePicker = this.$el;

            if (carrierId) {
                this._rpc({
                    route: "/shop/delivery_date_constraints",
                    params: {
                        carrier_id: carrierId,
                    },
                }).then(function (result) {
                    if (result.min_date && typeof $.fn.datetimepicker !== "undefined") {
                        $datePicker
                            .data("DateTimePicker")
                            .minDate(new Date(result.min_date));
                    }
                    if (result.max_date && typeof $.fn.datetimepicker !== "undefined") {
                        $datePicker
                            .data("DateTimePicker")
                            .maxDate(new Date(result.max_date));
                    }
                });
            }
        },

        _onDeliveryDateChange: function (ev) {
            var self = this;
            var $input = $(ev.currentTarget);
            var carrierId = $('input[name="delivery_type"]:checked').val();

            if (carrierId) {
                this._rpc({
                    route: "/shop/validate_delivery_date",
                    params: {
                        carrier_id: carrierId,
                        delivery_date: $input.val(),
                    },
                }).then(function (result) {
                    if (!result.valid) {
                        $input.val("");
                        $input.after(
                            $('<div class="alert alert-warning">').text(result.message)
                        );
                    }
                });
            }
        },
    });
});
