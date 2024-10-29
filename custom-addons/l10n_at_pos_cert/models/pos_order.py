from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    l10n_at_fiskaly_transaction_uuid = fields.Char(string="Transaction ID", readonly=True, copy=False)
    l10n_at_receipt_type = fields.Char(string="Receipt Type", readonly=True, copy=False)
    l10n_at_receipt_number = fields.Char(string="Receipt Number", readonly=True,
                                         copy=False)  # receipt number : "3" for example -> Char
    l10n_at_qr_code_data = fields.Char(string="QR Code Data", readonly=True, copy=False)
    l10n_at_time_signature = fields.Integer(string="Time Signature", readonly=True, copy=False)
    l10n_at_cash_register_id = fields.Char(string="Cash Register ID", readonly=True, copy=False)
    l10n_at_cash_register_serial_number = fields.Char(string="Cash Register Serial Number", readonly=True, copy=False)
    l10n_at_signature_creation_unit_id = fields.Char(string="Signature Creation Unit ID", readonly=True, copy=False)

    @api.model
    def _order_fields(self, ui_order):
        fields = super()._order_fields(ui_order)
        if self.env.company.l10n_at_austria() and ui_order.get('l10n_at_fiskaly_transaction_uuid'):
            fields['l10n_at_fiskaly_transaction_uuid'] = ui_order['l10n_at_fiskaly_transaction_uuid']
            fields['l10n_at_receipt_type'] = ui_order['l10n_at_receipt_type']
            fields['l10n_at_receipt_number'] = ui_order['l10n_at_receipt_number']
            fields['l10n_at_qr_code_data'] = ui_order['l10n_at_qr_code_data']
            fields['l10n_at_time_signature'] = ui_order['l10n_at_time_signature']
            fields['l10n_at_cash_register_id'] = ui_order['l10n_at_cash_register_id']
            fields['l10n_at_cash_register_serial_number'] = ui_order['l10n_at_cash_register_serial_number']
            fields['l10n_at_signature_creation_unit_id'] = ui_order['l10n_at_signature_creation_unit_id']

        return fields

    def _export_for_ui(self, order):
        json = super()._export_for_ui(order)

        if self.env.company.l10n_at_austria():
            receipt_info = {
                '_id': order.l10n_at_fiskaly_transaction_uuid,
                'receipt_type': order.l10n_at_receipt_type,
                'receipt_number': order.l10n_at_receipt_number,
                'qr_code_data': order.l10n_at_qr_code_data,
                'time_signature': order.l10n_at_time_signature,
                'cash_register_id': order.l10n_at_cash_register_id,
                'cash_register_serial_number': order.l10n_at_cash_register_serial_number,
                'signature_creation_unit_id': order.l10n_at_signature_creation_unit_id
            }
            json['receipt_info'] = receipt_info

        return json  # return json file with all the information regarding the receipt that should be included in the terminal receipt.
