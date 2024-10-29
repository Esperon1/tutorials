/** @odoo-module */

// import {Order} from "@point_of_sale/app/store/models";
import {qrCodeSrc, uuidv4} from "@point_of_sale/utils";
import {convertFromEpoch} from "@l10n_at_pos_cert/app/utils";
import {patch} from "@web/core/utils/patch";

patch(Order.prototype, { // https://www.odoo.com/documentation/17.0/developer/reference/frontend/patching_code.html
    setup() {
        super.setup(...arguments);
        if (this.pos.isCountryAustriaAndFiskaly()) {
            console.log('AT Fiscalization');
            this.transactionState = this.transactionState || 'inactive';
            this.save_to_db();
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


    /*
 *  Return an array of { 'vat_rate': ..., 'amount': ...}
 */
    _createAmountPerVatRateArray() {
        if (!this.pos.isCountryAustriaAndFiskaly()) {
            return super._createAmountPerVatRateArray(...arguments);
        }
        const rateIds = {
            STANDARD: [],
            REDUCED_1: [],
            REDUCED_2: [],
            SPECIAL: [],
            ZERO: []
        };
        this.get_tax_details().forEach((detail) => {
            rateIds[this.pos.vatRateMapping[detail.tax.amount]].push(detail.tax.id);
        });
        const amountPerVatRate = {
            STANDARD: 0,
            REDUCED_1: 0,
            REDUCED_2: 0,
            SPECIAL: 0,
            ZERO: 0,
        };
        for (var rate in rateIds) {
            rateIds[rate].forEach((id) => {
                amountPerVatRate[rate] += this.get_total_for_taxes(id);
            });
        }
        console.log(rateIds);
        console.log(amountPerVatRate);
        return Object.keys(amountPerVatRate)
            .filter((rate) => !!amountPerVatRate[rate])
            .map((rate) => ({
                vat_rate: rate,
                amount: amountPerVatRate[rate].toFixed(2) //TODO: this.env.utils.roundCurrency(amountPerVatRate[rate]).toFixed(2),
            }));
    },
    /*
     *  Return an array of { 'payment_type': ..., 'amount': ...}
     */
    _createAmountPerPaymentTypeArray() {
        if (!this.pos.isCountryAustriaAndFiskaly()) {
            return super._createAmountPerPaymentTypeArray(...arguments);
        }

        const amountPerPaymentTypeArray = [];
        this.get_paymentlines().forEach((line) => {
            amountPerPaymentTypeArray.push({
                payment_type:
                    line.payment_method.name.toLowerCase() === "cash" ? "CASH" : "NON_CASH",
                amount: line.amount.toFixed(2) //TODO: fix env.utils error: this.env.utils.roundCurrency(line.amount).toFixed(2),
            });
        });
        let change = this.get_change();
        if (change) {
            change = -this.get_change()
            amountPerPaymentTypeArray.push({
                payment_type: "CASH",
                amount: change.toFixed(2).toString() //TODO: this.env.utils.roundCurrency(-change).toFixed(2),
            });
        }
        return amountPerPaymentTypeArray;
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
                    // Need to update the token
                    await this._authenticate();
                    return this.createTransaction();
                }
                // Return a Promise with rejected value for errors that are not handled here
                return Promise.reject(error);
            });
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
    //@Override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (this.pos.isCountryAustriaAndFiskaly()) {
            if (this.isTransactionFinished()) {
                json['l10n_at_fiskaly_transaction_uuid'] = this.fiskalyUuid;
                json['l10n_at_receipt_type'] = this.l10n_at_data['receipt_type'];
                json['l10n_at_receipt_number'] = this.l10n_at_data['receipt_number'];
                json['l10n_at_qr_code_data'] = this.l10n_at_data['qr_code_data'];
                json['l10n_at_time_signature'] = this.l10n_at_data['time_signature'];
                json['l10n_at_cash_register_id'] = this.l10n_at_data['cash_register_id'];
                json['l10n_at_cash_register_serial_number'] = this.l10n_at_data['cash_register_serial_number'];
                json['l10n_at_signature_creation_unit_id'] = this.l10n_at_data['signature_creation_unit_id'];
            }
        }
        return json;
    },

    // @Override
    export_for_printing() {
        const receipt = super.export_for_printing(...arguments);
        if (this.pos.isCountryAustriaAndFiskaly()) {
            if (this.isTransactionFinished()) {
                receipt["l10n_at_receipt_number"] = this.l10n_at_data["receipt_number"];
                receipt["l10n_at_time_signature"] = convertFromEpoch(this.l10n_at_data["time_signature"]);
                receipt["l10n_at_cash_register_serial_number"] = this.l10n_at_data["cash_register_serial_number"];
                receipt["l10n_at_qr_code"] = qrCodeSrc(this.l10n_at_data["qr_code_data"]);
            }
        }
        return receipt;
    },
});

