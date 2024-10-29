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
        return this.transactionState === 'inactive';
    },
    transactionStarted() {
        this.transactionState = 'started';
    },
    isTransactionStarted() {
        return this.transactionState === 'started';
    },
    transactionFinished() {
        this.transactionState = 'finished';
    },
    isTransactionFinished() {
        return this.transactionState === 'finished';
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

    async createTransaction() {
        if (!this.pos.getApiToken()) {
            await this._authenticate(); //  If there's an error, a promise is created with a rejected value
        }

        const at_transactionUuid = uuidv4();
        const amountPerVatRateArray = this._createAmountPerVatRateArray();
        const amountPerPaymentTypeArray = this._createAmountPerPaymentTypeArray();
        const lineItemsArray = this._createLineItemsArray();

        const payload = {
            'cash_register_id': this.pos.cash_register_id,
            'receipt_id': at_transactionUuid,
            "receipt_type": "NORMAL",
            "schema": {
                "standard_v1": {
                    "amounts_per_vat_rate": amountPerVatRateArray,
                    "amounts_per_payment_type": amountPerPaymentTypeArray,
                    "line_items": lineItemsArray
                }
            }
        }
        const data = {}
        return $.ajax({
            url: `${this.pos.getApiUrl()}/cash-register/${this.pos.get_at_CashRegisterId()}/receipt/${at_transactionUuid}`,
            method: "PUT",
            data: JSON.stringify(payload),
            contentType: "application/json",
            headers: {Authorization: `Bearer ${this.pos.getApiToken()}`},
            timeout: 5000,
        })
            .then((data) => {
                this.fiskalyUuid = at_transactionUuid; // Not sure if this is needed
                this.l10n_at_data = data; // store all the data for the receipt.
                this.transactionFinished();
            })
            .catch(async (error) => {
                if (error.status === 401) {
                    await this._authenticate();
                    return this.createTransaction();
                }
                return Promise.reject(error);
            });
    },

    // @Override
    _createAmountPerVatRateArray(order) {
        const rateIds = {
            STANDARD: [],
            REDUCED_1: [],
            REDUCED_2: [],
            SPECIAL: [],
            ZERO: [],
        };
        order.get_tax_details().forEach((detail) => {
            rateIds[this.vatRateMapping[detail.tax_percentage]].push(detail.id);
        });
        const amountPerVatRate = {
            STANDARD: 0,
            REDUCED_1: 0,
            REDUCED_2: 0,
            SPECIAL: 0,
            ZERO: 0,
        };
        for (let rate in rateIds) {
            rateIds[rate].forEach((id) => {
                amountPerVatRate[rate] += order.get_total_for_taxes(id);
            });
        }
        return Object.keys(amountPerVatRate)
            .filter((rate) => !!amountPerVatRate[rate])
            .map((rate) => ({
                vat_rate: rate,
                amount: roundCurrency(amountPerVatRate[rate], this.currency).toFixed(2),
            }));
    },

    _createAmountPerPaymentTypeArray() {
        if (!this.isCountryAustriaAndFiskaly()) {
            return super._createAmountPerPaymentTypeArray(...arguments);
        }

        const amountPerPaymentTypeArray = [];
        this.payment_ids.forEach((line) => {
            amountPerPaymentTypeArray.push({
                payment_type:
                    line.payment_method.name.toLowerCase() === "cash" ? "CASH" : "NON_CASH",
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
    _createLineItemsArray() {
        const lines = [];
        this.get_orderlines().forEach((line) => {
            lines.push({
                price_per_unit: line.price.toFixed(2),
                quantity: line.quantity,
                text: line.product.display_name
            });
        });
        return lines;
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