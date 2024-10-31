import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {convertFromEpoch} from "@l10n_at_pos_cert/app/utils";
import {patch} from "@web/core/utils/patch";
import {roundCurrency} from "@point_of_sale/app/models/utils/currency";

patch(PosOrder.prototype, {

    // @Override
    setup() {
        super.setup(...arguments);
        if (this.isCountryAustriaAndFiskaly()) {
            console.log('AT Fiscalization');
            this.transactionState = this.transactionState || 'inactive';
        }
    },
    _initReceiptInformation() {
        return {
            _id: {"_id": null},
            _type: {"_type": "RECEIPT"},
            _env: {"_env": "PRODUCTION"},
            _version: {"_version": "0.1"},
            _signed: {"signed": false}, // TODO
            _receipt_type: {"receipt_type": "NORMAL"},
            _serial_number: {"serial_number": null},
            _receipt_number: {"receipt_number": null},
            _time_signature: {"time_signature": null},
            _qr_code_data: {"qr_code_data": ''},
            _metadata: {
                "metadata": {
                    "valid_property": "ABCDF12345XCVB",
                    "add_val_property": "'LKJHGF12345XCV"
                }
            },
            _hints: {"hints": []}
        };
    },

    isTransactionInactive() {
        return this.transactionState === "inactive";
    },
    transactionStarted() {
        this.transactionState = "started";
    },
    isTransactionStarted() {
        return this.transactionState === "started";
    },
    transactionFinished() {
        this.transactionState = "finished";
    },
    isTransactionFinished() {
        return this.transactionState === "finished";
    },

    isCountryAustria() {
        return this.config.is_company_country_austria;
    },

    isCountryAustriaAndFiskaly() {
        return this.isCountryAustria()
    },

    _authenticate() {
        const data = {
            api_key: this.pos.getApiKey(),
            api_secret: this.pos.getApiSecret(),
        };

        return $.ajax({
            url: this.pos.getApiUrl() + "/auth",
            method: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            timeout: 5000,
        })
            .then((data) => {
                this.pos.setApiToken(data.access_token);
            })
            .catch((error) => {
                error.source = "authenticate";
                return Promise.reject(error);
            });
    },

    // @Override
    _createAmountPerPaymentTypeArray() {
        const amountPerPaymentTypeArray = [];
        this.payment_ids.forEach((line) => {
            amountPerPaymentTypeArray.push({
                payment_type:
                    line.payment_method_id.name.toLowerCase() === "cash" ? "CASH" : "NON_CASH",
                amount: roundCurrency(line.amount, this.currency).toFixed(2) //TODO: fix env.utils error: this.env.utils.roundCurrency(line.amount).toFixed(2),
            });
        });
        const change = this.get_change();
        if (change) {
            amountPerPaymentTypeArray.push({
                payment_type: "CASH",
                amount: roundCurrency(-change, this.currency).toFixed(2),
            });
        }
        return amountPerPaymentTypeArray;
    },

    export_for_printing() {
        const receipt = super.export_for_printing(...arguments);
        if (this.isCountryAustriaAndFiskaly()) {
            if (this.isTransactionFinished()) {
                receipt["l10n_at_receipt_number"] = this.l10n_at_data["receipt_number"];
                receipt["l10n_at_time_signature"] = convertFromEpoch(this.l10n_at_data["time_signature"]);
                receipt["l10n_at_cash_register_serial_number"] = this.l10n_at_data["cash_register_serial_number"];
                receipt["l10n_at_qr_code"] = qrCodeSrc(this.l10n_at_data["qr_code_data"]);
            } else {
                console.error("Transaction not finished"); // Continue from here
            }
        }
        return receipt;
    },

});

export function qrCodeSrc(url, {size = 200} = {}) {
    return `/report/barcode/QR/${encodeURIComponent(url)}?width=${size}&height=${size}`;
}