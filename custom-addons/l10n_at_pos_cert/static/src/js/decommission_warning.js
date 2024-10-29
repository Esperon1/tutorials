/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Dialog} from "@web/core/dialog/dialog";
import {FormController} from "@web/views/form/form_controller";


patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
    },

    _onDecommissionSCU(event) {
        event.stopPropagation();
        const self = this;

        Dialog.confirm(this, {
            title: "Confirm",
            body: "<strong>Are you sure you want to Decommission SCU?</strong><br/><strong>You will NOT</strong> be able to use the previous SCU ID.",
            confirm_callback: function () {
                self._rpc({
                    model: 'res.company',
                    method: 'action_decommission_scu',
                    args: [[self.model.get(this.handle).data.id]],
                }).then(function () {
                    self.reload();
                });
            },
            cancel_callback: function () {
                console.log('Action cancelled');
            }
        });
    },
});