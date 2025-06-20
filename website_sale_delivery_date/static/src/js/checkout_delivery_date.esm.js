import {parseDate} from "@web/core/l10n/dates";
import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

const WebsiteSaleCheckout = publicWidget.registry.WebsiteSaleCheckout;

WebsiteSaleCheckout.include({
    disabledInEditableMode: true,

    async start() {
        this.pickerElement = this.el.querySelector(
            "[data-widget='delivery-date-picker']"
        );
        this.$pickerElement = $(this.pickerElement);
        this.$pickerError = this.$el.find("#datetimePickerError");
        this.picker = this.call("datetime_picker", "create", {
            target: this.pickerElement,
            onApply: this._onChangeDatePicker.bind(this),
            format: "yyyy-MM-dd HH:mm",
            pickerProps: {
                type: "datetime",
                minDate: luxon.DateTime.now(),
                rounding: 30,
            },
        });
        this.picker.enable();
        await this._super(...arguments);
    },

    async _onChangeDatePicker(newDate) {
        const carrierEl = this.el.querySelector(
            'input[name="o_delivery_radio"]:checked'
        );
        const carrierId = parseInt(carrierEl.dataset.dmId, 10);
        if (!carrierId || !newDate) return;
        const result = await rpc("/shop/set_delivery_date", {
            carrier_id: carrierId,
            delivery_date: newDate.toFormat("yyyy-MM-dd HH:mm"),
        });
        let error = "";
        if (result.valid) {
            this.$pickerElement.removeClass("is-invalid").addClass("is-valid");
        } else {
            this.$pickerElement.val("").addClass("is-invalid").removeClass("is-valid");
            error = result.message;
        }
        this.$pickerError.text(error);
    },

    async _updateDeliveryMethod(radio) {
        await this._super(...arguments);
        await this._updateDeliveryDate(radio.dataset.dmId);
    },

    async _updateDeliveryDate(dmId) {
        const carrierId = parseInt(dmId, 10);
        if (!carrierId) return;
        const result = await rpc("/shop/delivery_date_constraints", {
            carrier_id: carrierId,
        });
        this.$pickerElement.val("").removeClass("is-invalid is-valid");
        this.$pickerError.text("");
        if (result.min_date) {
            this.picker.state.minDate = parseDate(result.min_date);
        }
        if (result.max_date) {
            this.picker.state.maxDate = parseDate(result.max_date);
        }
    },

    destroy() {
        this.picker();
        return this._super(...arguments);
    },
});
