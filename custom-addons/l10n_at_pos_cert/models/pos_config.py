from odoo import models, fields, api, _
from odoo.addons.l10n_at_pos_cert.utils.fiskaly_api import FiskalyAPI
from odoo.exceptions import UserError
import uuid


class PosConfig(models.Model):
    _name = 'pos.config'
    _inherit = ['pos.config', 'mail.thread']

    l10n_at_scu_id = fields.Char(related='company_id.l10n_at_scu_id', readonly=True)
    l10n_at_cash_register_id = fields.Char('Fiskaly Cash Register ID', readonly=True)
    l10n_at_cash_register_state = fields.Selection([
        ('CREATED', 'Created'),
        ('REGISTERED', 'Registered'),
        ('INITIALIZED', 'Initialized'),
        ('DECOMMISSIONED', 'Decommissioned'),
        ('OUTAGE', 'Outage'),
        ('DEFECTIVE', 'Defective')], 'Cash Register State', readonly=True)

    l10n_at_cash_register_serial_number = fields.Char('Cash Register Serial Number', readonly=True)
    l10_at_receipt_id = fields.Char('Receipt ID', readonly=True)
    is_company_country_austria = fields.Boolean(string='Company located in Austria',
                                                related='company_id.is_country_austria')

    l10n_at_create_cash_register = fields.Boolean('Create Cash Register', default=False)

    # DEP7 Data Export and Audit Wizard
    l10n_at_end_time_signature = fields.Integer(string="End Receipt Time Signature")
    l10n_at_start_time_signature = fields.Integer(string="Start Receipt Time Signature")
    l10n_at_end_receipt_number = fields.Char(string="End Receipt Number")
    l10n_at_start_receipt_number = fields.Char(string="Start Receipt Number")

    def action_open_wizard(self):
        return self.env.ref('l10n_at_pos_cert.action_dep7_data_export_audit_wizard').read()[0]

    @api.model_create_multi
    def create(self, vals_list):
        pos_configs = super().create(vals_list)
        for pos_config in pos_configs:
            if pos_config.l10n_at_create_cash_register:
                pos_config.action_generate_cash_register()
        return pos_configs

    def write(self, values):
        res = super().write(values)
        for config in self:
            if values.get('l10n_at_create_cash_register') and not config.l10n_at_cash_register_id:
                config.action_generate_cash_register()
        return res

    def action_archive(self):
        res = super().action_archive()
        cr_to_disable_data = [(config.company_id, config.l10n_at_cash_register_id)
                              for config in self if config.l10n_at_cash_register_id]
        for company, cash_register_id in cr_to_disable_data:
            self.action_decommission_cash_register(company, cash_register_id)
            res.write({'l10n_at_cash_register_id': False})
        return res

    def _l10n_at_check_fiskaly_api_key_secret(
            self):  # Helper function to check if the Fiskaly API key and secret are set in the company settings
        if not self.company_id.sudo().l10n_at_fiskaly_api_key or not self.company_id.sudo().l10n_at_fiskaly_api_secret:
            raise UserError(_("You have to set your Fiskaly key and secret in your company settings."))

    @api.model
    def l10n_at_get_fiskaly_urls_and_key_secret(self, config_id):  # used in pos_store.js
        self.browse().check_access('read')
        company = self.browse(config_id).company_id.sudo()
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
        api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'api_base_url': self.env['res.company']._l10n_at_fiskaly_api_base_url(),
        }

    def action_generate_cash_register(self):
        for config in self:
            if config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )
            cash_register_id = str(uuid.uuid4())
            api.cash_register_id = self.l10n_at_cash_register_id
            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise UserError(_("FON authentication failed."))
            cash_register = api.l10n_at_create_cash_register(cash_register_id)
            config.write({'l10n_at_cash_register_id': cash_register_id})
            cr_data = api.l10n_at_retrieve_cash_register(cash_register_id)
            config.l10n_at_cash_register_state = cr_data['state']
            config.l10n_at_cash_register_serial_number = cr_data['serial_number']

    def action_update_cash_register_state(self, state: str):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise Exception("FON authentication failed.")
            api.l10n_at_update_cash_register(config.l10n_at_cash_register_id, state)
            config.l10n_at_cash_register_state = state

    def action_check_for_outage(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise Exception("FON authentication failed.")
            config.l10n_at_cash_register_state = api.l10n_at_retrieve_cash_register(config.l10n_at_cash_register_id)[
                'state']

    def action_list_all_cash_registers(self):
        for config in self:
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise Exception("FON authentication failed.")
            api.l10n_at_list_cash_register()

    def action_retrieve_and_update_metadata_cash_register(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise Exception("FON authentication failed.")
            api.l10n_at_retrieve_metadata_cash_register(config.l10n_at_cash_register_id)
            api.l10n_at_update_metadata_cash_register(config.l10n_at_cash_register_id)

    def action_sign_receipt(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )
            api.receipt_id = self.l10_at_receipt_id

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise Exception("FON authentication failed.")
            api.l10n_at_sign_receipt(config.l10n_at_cash_register_id, config.l10_at_receipt_id)
            api.l10n_at_retrieve_receipt(config.l10n_at_cash_register_id, config.l10_at_receipt_id)
            api.l10n_at_list_all_receipts(config.l10n_at_cash_register_id)
            api.l10n_at_list_receipt_cash_register(config.l10n_at_cash_register_id)
            api.l10n_at_retrieve_metadata_receipt(config.l10n_at_cash_register_id, config.l10_at_receipt_id)
            api.l10n_at_update_metadata_receipt(config.l10n_at_cash_register_id, config.l10_at_receipt_id)
            if api.l10n_at_validate_receipt(config.l10n_at_cash_register_id, config.l10_at_receipt_id)[
                'validation_result'] != 'SUCCESS':
                raise Exception("Receipt validation failed.")

    def action_audit_data_export(self, params):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )
            params = {
                'start_receipt_number': params['l10n_at_start_receipt_number'] if params[
                    'l10n_at_start_receipt_number'] else '0',
                'end_receipt_number': params['l10n_at_end_receipt_number'] if params[
                    'l10n_at_end_receipt_number'] else '0',
                'start_time_signature': params['l10n_at_start_time_signature'] if params[
                    'l10n_at_start_time_signature'] else 0,
                'end_time_signature': params['l10n_at_end_time_signature'] if params[
                    'l10n_at_end_time_signature'] else 0,
            }

            return api.l10n_at_export_data(config.l10n_at_cash_register_id, params)

    def action_decommission_scu(self):

        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )
            api.scu_id = self.l10n_at_scu_id
            api.l10n_at_decommission_scu(config.l10n_at_scu_id)

    @api.model  # Operates on a recod that doesn't need to depend on specific record's fields. Call method directly on the model itself.
    def action_decommission_cash_register(self, company, cash_register_id):
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
        api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
        api = FiskalyAPI(api_key=api_key,
                         api_secret=api_secret,
                         fon_participant_id=company.l10n_at_fon_participant,
                         fon_user_id=company.l10n_at_fon_user_id,
                         fon_user_pin=company.l10n_at_fon_pin,
                         legal_entity_id={
                             'legal_entity_id': {
                                 company.l10n_at_legal_entity_type: company.l10n_at_legal_entity}}
                         )
        api.l10n_at_decommission_cash_register(cash_register_id)

    def action_transition_cash_register_to_outage(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            api.cash_register_id = self.l10n_at_cash_register_id
            api.l10n_at_transition_to_outage(config.l10n_at_cash_register_id)

    def action_transition_back_to_initialised(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            api.cash_register_id = self.l10n_at_cash_register_id
            api.l10n_at_transition_to_initiallised(config.l10n_at_cash_register_id)

    def action_transition_to_defective_cash_register(self):
        for config in self:
            if not config.l10n_at_cash_register_id:
                continue
            IrParamSudo = self.env['ir.config_parameter'].sudo()
            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.company_id.l10n_at_fon_participant,
                             fon_user_id=self.company_id.l10n_at_fon_user_id,
                             fon_user_pin=self.company_id.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {
                                     self.company_id.l10n_at_legal_entity_type: self.company_id.l10n_at_legal_entity}}
                             )

            api.cash_register_id = self.l10n_at_cash_register_id
            api.l10n_at_transition_to_defective_cash_register(config.l10n_at_cash_register_id)
