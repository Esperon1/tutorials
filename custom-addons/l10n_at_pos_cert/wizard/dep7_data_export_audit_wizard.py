from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import base64


class Dep7DataExportAuditWizard(models.TransientModel):
    _name = "dep7.data.export.audit.wizard"
    _description = "DEP7 Audit Wizard"

    l10n_at_start_receipt_number = fields.Char(string="Start Receipt Number", required=False,
                                               help='Only return receipts with a Receipt Number greater than or equal to the given value.')
    l10n_at_end_receipt_number = fields.Char(string="End Receipt Number", required=False,
                                             help='Only return receipts with a Receipt Number less than or equal to the given value.')
    l10n_at_start_time_signature = fields.Integer(string="Start Receipt Time Signature", required=False,
                                                  help='Only return receipts with a Time Signature later than or equal to the given timestamp.')
    l10n_at_end_time_signature = fields.Integer(string="End Receipt Time Signature", required=False,
                                                help='Only return receipts with a Time Signature earlier than or equal to the given timestamp.')

    l10n_at_receipts_export_data = fields.Binary(string="File", readonly=True)
    l10n_at_receipts_export_filename = fields.Char(string="Filename", readonly=True)

    def action_export_audit(self):
        self.ensure_one()
        record_id = self.env.context.get('active_id')
        record = self.env['pos.config'].browse(record_id)
        params = {
            'l10n_at_start_receipt_number': self.l10n_at_start_receipt_number,
            'l10n_at_end_receipt_number': self.l10n_at_end_receipt_number,
            'l10n_at_start_time_signature': self.l10n_at_start_time_signature,
            'l10n_at_end_time_signature': self.l10n_at_end_time_signature,
        }

        response = record.action_audit_data_export(params)
        if not response:
            raise UserError(_('No data found for the given criteria.'))

        file_content = json.dumps(response, indent=4).encode('utf-8')

        attachment = self.env['ir.attachment'].create({
            'name': 'audit_data_export.json',
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'res_model': record._name,
            'res_id': record.id,
        })

        record.message_post(body=_('Audit data exported.'), attachment_ids=attachment.ids)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
