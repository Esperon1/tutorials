/** @odoo-module */

import {offlineErrorHandler} from "@point_of_sale/app/errors/error_handlers"
import {patch} from "@web/core/utils/patch";
import {_t} from "@web/core/l10n/translation";
import {PosStore} from "@point_of_sale/app/store/pos_store";


// import {Order} from "@point_of_sale/app/store/models";

// import {ErrorPopup} from "@point_of_sale/app/errors/popups/error_popup";
// import {ConfirmPopup} from "@point_of_sale/app/utils/confirm_popup/confirm_popup";


patch(PosStore.prototype, {
    async setup() { // fetch necessary data from the pod_config.py
        this.access_token = '';
        this.vatRateMapping = {
            20: "STANDARD",
            10: "REDUCED_1",
            13: "REDUCED_2",
            19: "SPECIAL",
            0: "ZERO",
        };
        try {
            await super.setup(...arguments);
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                console.log('Connection Lost')
            }
        }
    },

    // async after_load_server_data() { // Load the data from the server
    //     if (this.isCountryAustriaAndFiskaly()) {
    //         try {
    //             await this.env.services.orm
    //                 .call('pos.config', 'l10n_at_get_fiskaly_urls_and_key_secret', [this.config.id])
    //                 .then((data) => {
    //                     this.company.l10n_at_api_key = data['api_key'];
    //                     this.company.l10n_at_api_secret = data['api_secret'];
    //                     this.apiUrl = data['api_base_url'];
    //
    //                     return this.initReceipt(); // Perhaps this should be called authenticate FiskalyAPI
    //                 })
    //         } catch (error) {
    //             if (error.status === 0) {
    //                 this.showFiskalyNoInternetConfirmPopup(this);
    //             } else {
    //                 const message = {
    //                     unknown: _t("An unknown error has occurred! Please, contact Odoo."),
    //                 };
    //                 this.fiskalyError(error, message);
    //             }
    //         }
    //     }
    //     return super.after_load_server_data(...arguments);
    // },

    // async showFiskalyNoInternetConfirmPopup(event) {
    //     const {confirmed} = await this.popup.add(ConfirmPopup, {
    //         title: _t("Problem with internet"),
    //         body: _t(
    //             "You can either wait for the connection issue to be resolved or continue with a non-compliant receipt (the order will still be sent to Fiskaly once the connection issue is resolved).\n" +
    //             "Do you want to continue with a non-compliant receipt?"
    //         ),
    //     });
    //     if (confirmed) {
    //         event.detail();
    //     }
    // },

    getApiToken() {
        return this.access_token;
    },
    setApiToken(access_token) {
        this.access_token = access_token;
    },
    getApiUrl() {
        return this.apiUrl;
    },
    getApiKey() {
        if (this.isCountryAustriaAndFiskaly()) {
            return this.company.l10n_at_api_key;
        } else {
            return super.getApiKey();
        }
    },
    getApiSecret() {
        return this.company.l10n_at_api_secret;
    },

    get_at_CashRegisterId() {
        console.log(this.config.l10n_at_cash_register_id)
        return this.config.l10n_at_cash_register_id;
    },
    getSCUId() {
        return this.config.l10n_at_scu_id;
    },
    isCountryAustria() {
        return this.config.is_company_country_austria;
    },
    isCountryAustriaAndFiskaly() {
        return this.isCountryAustria() // && !! could be something missing here.
    },

    initReceipt(url) {
        const data = {
            'api_key': this.company.l10n_at_api_key,
            'api_secret': this.company.l10n_at_api_secret
        };
        url = this.getApiUrl();
        return $.ajax({
            url: `${url}/auth`,
            method: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            timeout: 5000,
        }).then((data) => {
            const access_token = data.access_token;
            this.setApiToken(access_token)
        }).catch((error) => {
            error.source = "authenticate";
            return Promise.reject(error);
        });

    },

    //@Override
    /**
     * This function first attempts to send the orders remaining in the queue to Fiskaly before trying to
     * send it to Odoo. Two cases can happen:
     * - Failure to send to Fiskaly => we assume that if one order fails, EVERY order will fail
     * - Failure to send to Odoo => the order is already sent to Fiskaly, we store them locally with the TSS info
     */
    async _flush_orders(orders, options) {
        if (!this.isCountryAustriaAndFiskaly()) {
            return super._flush_orders(...arguments);
        }
        if (!orders || !orders.length) {
            return Promise.resolve([]);
        }

        const orderObjectMap = {};
        for (const orderJson of orders) {
            orderObjectMap[orderJson["id"]] = new Order(
                {env: this.env},
                {pos: this, json: orderJson["data"]} // map each JSON order to the Order object
            );
        }

        let l10nAtFiskalyError;
        const sentToFiskaly = [];
        const fiskalyFailure = [];
        const ordersToUpdate = {};
        for (const orderJson of orders) {
            try {
                const orderObject = orderObjectMap[orderJson["id"]];
                if (!l10nAtFiskalyError) { // if no error has been thrown yet
                    if (orderObject.isTransactionInactive()) { // if the transaction is inactive
                        await orderObject.createTransaction(); // create a transaction
                        ordersToUpdate[orderJson["id"]] = true; // mark the order as updated
                    }
                }
                if (orderObject.isTransactionFinished()) { // if the transaction is finished
                    sentToFiskaly.push(orderJson); // add the order to the list of orders sent to Fiskaly
                } else {
                    fiskalyFailure.push(orderJson); // add the order to the list of orders that failed to send to Fiskaly
                }
            } catch (error) { // if an error is thrown
                l10nAtFiskalyError = error;
                l10nAtFiskalyError.code = "fiskaly";
                fiskalyFailure.push(orderJson);
            }
        }

        let result, odooError;
        if (sentToFiskaly.length > 0) { // if there are orders that have been sent to Fiskaly
            for (const orderJson of sentToFiskaly) { // for each order that has been sent to Fiskaly
                if (ordersToUpdate[orderJson["id"]]) { // if the order has been updated
                    orderJson["data"] = orderObjectMap[orderJson["id"]].export_as_JSON(); // update the JSON order with our fetched data
                }
            }
            try {
                result = await super._flush_orders(...arguments); // send the orders to Odoo
            } catch (error) {
                odooError = error;
            }
        }
        if (result && fiskalyFailure.length === 0) { // if all orders have been sent to Odoo
            return result;
        } else {
            if (Object.keys(ordersToUpdate).length) {
                for (const orderJson of fiskalyFailure) {
                    if (ordersToUpdate[orderJson["id"]]) {
                        orderJson["data"] = orderObjectMap[orderJson["id"]].export_as_JSON(); // update the JSON order with our fetched data
                    }
                }
                const ordersToSave =
                    result && result.length ? fiskalyFailure : fiskalyFailure.concat(sentToFiskaly);
                this.db.save("orders", ordersToSave); // save the orders locally to a database.
            }
            this.set_synch("disconnected");
            throw odooError || l10nAtFiskalyError ;
        }
    },
    // async l10nAtFiskalyError(error, message) {
    //     if (error.status === 0) {
    //         const title = _t("No internet");
    //         const body = message.noInternet;
    //         await this.popup.add(offlineErrorHandler, {title, body});
    //     } else if (error.status === 401 && error.source === "authenticate") {
    //         await this.l10n_at_showUnauthorizedPopup();
    //     } else if (
    //         (error.status === 400 && error.responseJSON.message.includes("tss_id")) ||
    //         (error.status === 404 && error.responseJSON.code === "E_TSS_NOT_FOUND")
    //     ) {
    //         await this.l10n_at__showBadRequestPopup("TSS ID");
    //     } else if (
    //         (error.status === 400 && error.responseJSON.message.includes("client_id")) ||
    //         (error.status === 400 && error.responseJSON.code === "E_CLIENT_NOT_FOUND")
    //     ) {
    //         // the api is actually sending an 400 error for a "Not found" error
    //         await this.l10n_at__showBadRequestPopup("Client ID");
    //     } else {
    //         const title = _t("Unknown error");
    //         const body = message.unknown;
    //         await this.popup.add(ErrorPopup, {title, body});
    //     }
    // },
    // async l10n_at__showBadRequestPopup(data) {
    //     const title = _t("Bad request");
    //     const body = _t("Your %s is incorrect. Update it in your PoS settings", data);
    //     await this.popup.add(ErrorPopup, {title, body});
    // },
    // async l10n_at_showUnauthorizedPopup() {
    //     const title = _t("Unauthorized error to Fiskaly");
    //     const body = _t(
    //         "It seems that your Fiskaly API key and/or secret are incorrect. Update them in your company settings."
    //     );
    //     await this.popup.add(ErrorPopup, {title, body});
    // },
})

