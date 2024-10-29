import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";
import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {ask} from "@point_of_sale/app/store/make_awaitable_dialog";
import {_t} from "@web/core/l10n/translation";
import {uuidv4} from "@point_of_sale/utils";
import {TaxError} from "@l10n_at_pos_cert/app/errors";
import {roundCurrency} from "@point_of_sale/app/models/utils/currency";

const RATE_ID_MAPPING = {
    20: "STANDARD",
    10: "REDUCED_1",
    13: "REDUCED_2",
    19: "SPECIAL",
    0: "ZERO",
};

patch(PosStore.prototype, {
    // @Overrideb
    async setup() {
        this.access_token = "";
        this.vatRateMapping = RATE_ID_MAPPING;
        await super.setup(...arguments);
    },
    // @Override
    async _onBeforeDeleteOrder(order) {
        try {
            if (this.isCountryAustriaAndFiskaly() && order.isTransactionStarted()) {
                await this.cancelTransaction(order);
            }
            return super._onBeforeDeleteOrder(...arguments);
        } catch (error) {
            const message = {
                noInternet: _t(
                    "Check the internet connection then try to validate or cancel the order. " +
                    "Do not delete your browsing, cookies and cache data in the meantime!"
                ),
                unknown: _t(
                    "An unknown error has occurred! Try to validate this order or cancel it again. " +
                    "Please contact Odoo for more information."
                ),
            };
            this.fiskalyError(error, message);
            return false;
        }
    },
    //@Override
    async afterProcessServerData() {
        if (this.isCountryAustriaAndFiskaly()) {
            const data = await this.data.call("pos.config", "l10n_at_get_fiskaly_urls_and_key_secret",
                [this.company.id]);

            this.company.l10n_at_fiskaly_api_key = data['api_key'];
            this.company.l10n_at_fiskaly_api_secret = data['api_secret'];
            this.apiUrl = data['api_base_url'];

        }
        return super.afterProcessServerData(...arguments);
    },
    async addLineToCurrentOrder(vals, opt = {}, configure = true) {
        if (this.isCountryAustriaAndFiskaly()) {
            const product = vals.product_id;
            for (const tax of product.taxes_id) {
                if (!(tax.amount in this.vatRateMapping)) {
                    throw new TaxError(product);
                }
            }
            if (!product.taxes_id.length) {
                throw new TaxError(product);
            }
        }
        return await super.addLineToCurrentOrder(vals, opt, configure);
    },
    async _authenticate() {
        const data = {
            api_key: this.company.l10n_at_api_key,
            api_secret: this.company.l10n_at_api_secret,
        };

        try {
            const response = await fetch(this.getApiUrl() + "/auth", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                const errorData = await response.json();
                const error = new Error(errorData.message || "Authentication failed");
                error.status = response.status;
                error.source = "authenticate";
                throw error;
            }
            const responseData = await response.json();
            this.setApiToken(responseData.access_token);
        } catch (error) {
            error.source = "authenticate";
            return Promise.reject(error);
        }
    },



    async fiskalyError(error, message) {
        if (error.status === 0) {
            const title = _t("No internet");
            const body = message.noInternet;
            this.dialog.add(AlertDialog, {title, body});
        } else if (error.status === 401 && error.source === "authenticate") {
            await this._showUnauthorizedPopup();
        } else {
            const title = _t("Unknown error");
            const body = message.unknown;
            this.dialog.add(AlertDialog, {title, body});
        }
    },

    async _showUnauthorizedPopup() {
        const title = _t("Unauthorized error to Fiskaly");
        const body = _t(
            "It seems that your Fiskaly API key and/or secret are incorrect. Update them in your company settings."
        );
        this.dialog.add(AlertDialog, {title, body});
    },

    async syncAllOrders(options = {}) {
        if (!this.isCountryAustriaAndFiskaly()) {
            return super.syncAllOrders(options);
        }

        const {orderToCreate, orderToUpdate} = this.getPendingOrder();
        const orders = [...orderToCreate, ...orderToUpdate];

        if (orders.length === 0) {
            return [];
        }

        const orderObjectMap = {};
        for (const order of orders) {
            orderObjectMap[order.id] = order;
        }

        let fiskalyError;
        const sentToFiskaly = [];
        const fiskalyFailure = [];
        const ordersToUpdate = {};
        for (const order of orders) {
            try {
                const orderObject = orderObjectMap[order.id];
                if (!fiskalyError) {
                    if (orderObject.isTransactionInactive()) {
                        await this.createTransaction(orderObject);
                        ordersToUpdate[order.id] = true;
                    }
                }
                if (orderObject.isTransactionFinished()) {
                    sentToFiskaly.push(order);
                } else {
                    fiskalyFailure.push(order);
                }
            } catch (error) {
                fiskalyError = error;
                fiskalyError.code = "fiskaly";
                fiskalyFailure.push(order);
            }
        }

        let result, odooError;
        if (sentToFiskaly.length > 0) {
            for (const orderJson of sentToFiskaly) {
                if (ordersToUpdate[orderJson["id"]]) {
                    orderJson["data"] = orderObjectMap[orderJson["id"]].serialize();
                }
            }
            try {
                result = await super.syncAllOrders(...arguments);
            } catch (error) {
                odooError = error;
            }
        }
        if (result && fiskalyFailure.length === 0) {
            return result;
        } else {
            if (Object.keys(ordersToUpdate).length) {
                for (const orderJson of fiskalyFailure) {
                    if (ordersToUpdate[orderJson["id"]]) {
                        orderJson["data"] = orderObjectMap[orderJson["id"]].serialize();
                    }
                }
            }
            throw odooError || fiskalyError;
        }
    },
    getApiToken() {
        return this.access_token;
    },
    setApiToken(token) {
        this.access_token = token;
    },
    getApiKey() {
        return this.company.l10n_at_api_key;
    },
    getApiSecret() {
        return this.company.l10n_at_api_secret;
    },
    getCashRegisterId() {
        return this.config.l10n_at_cash_register_id;
    },

    isCountryAustria() {
        return this.config.is_company_country_austria;
    },
    isCountryAustriaAndFiskaly() {
        return this.isCountryAustria() && !!this.getCashRegisterId();
    },

});
