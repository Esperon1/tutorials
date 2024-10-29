from odoo import models, fields, api, _
from odoo.addons.l10n_at_pos_cert.utils.fiskaly_api import FiskalyAPI
from odoo.exceptions import UserError, ValidationError
import uuid


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_at_fon_participant = fields.Char('FON Participant', help='Teilnehmneridentifikation in Finanzonline')
    l10n_at_fon_user_id = fields.Char('FON User ID', help='Benutzeridentifikation in Finanzonline')
    l10n_at_fon_pin = fields.Char('FON PIN', help='PIN für die Anmeldung in Finanzonline')
    l10n_at_legal_entity_type = fields.Selection(
        [('vat_id', 'UID'), ('tax_id', 'Steuernummer'), ('gln', 'Global Location Number')], 'Legal Entity Type',
        help='Rechtsträgerkennungstyp in Finanzonline')
    l10n_at_legal_entity = fields.Char('Legal Entity Number', help='Rechtsträgerkennung in Finanzonline')
    l10n_at_scu_id = fields.Char('Fiskaly SCU ID', readonly=True)
    is_country_austria = fields.Boolean('Company located in Austria', compute='_compute_is_country_austria')

    @api.depends('country_id')  # whether company is located in Austria based on the country_id.
    def _compute_is_country_austria(self):
        """Compute whether the company is located in Austria based on the country_id."""
        for company in self:
            company.is_country_austria = company.country_id.code == 'AT'

    @api.model
    def _l10n_at_fiskaly_api_base_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('l10n_at.fiskaly_api_base_url',
                                                                'https://rksv.fiskaly.com/api/v1')

    def l10n_at_austria(self):
        return self.is_country_austria

    def action_generate_scu(self):
        self.ensure_one()
        company = self
        if not company.l10n_at_scu_id:
            IrParamSudo = self.env['ir.config_parameter'].sudo()

            api_key = IrParamSudo.get_param('l10n_at.fiskaly_api_key')
            api_secret = IrParamSudo.get_param('l10n_at.fiskaly_api_secret')
            api = FiskalyAPI(api_key=api_key,
                             api_secret=api_secret,
                             fon_participant_id=self.l10n_at_fon_participant,
                             fon_user_id=self.l10n_at_fon_user_id,
                             fon_user_pin=self.l10n_at_fon_pin,
                             legal_entity_id={
                                 'legal_entity_id': {self.l10n_at_legal_entity_type: self.l10n_at_legal_entity}})
            if not api_key or not api_secret:
                raise UserError('Please set the Fiskaly API Key and Secret in the settings and try again')

            if not api.l10n_at_authenticate_fiskaly():
                raise UserError('Please check your API credentials and try again.')

            if api.l10n_at_authenticate_FON() != 'AUTHENTICATED':
                raise UserError("Please check your FON credentials and try again.")

            scu_id = str(uuid.uuid4())
            api.l10n_at_create_scu(scu_id)
            company.write({'l10n_at_scu_id': scu_id})
            api.l10n_at_retrieve_scu(company.l10n_at_scu_id)
            api.l10n_at_update_scu(company.l10n_at_scu_id)
            api.l10n_at_list_all_scu()
            api.l10n_at_retrieve_metadata_scu(company.l10n_at_scu_id)
            api.l10n_at_update_metadata_scu(company.l10n_at_scu_id)

        return {
            'name': _('Fiskaly SCU ID'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.company',
            'res_id': company.id,
            'target': 'current',
        }

    def action_decommission_scu(self):
        self.ensure_one()
        company = self
        if company.l10n_at_scu_id:
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
                                     company.l10n_at_legal_entity_type: company.l10n_at_legal_entity}})
            api.l10n_at_decommission_scu(company.l10n_at_scu_id)
            company.l10n_at_scu_id = False
        return {
            'name': _('Fiskaly SCU ID'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.company',
            'res_id': company.id,
            'target': 'current',
        }

    def action_archive(self):
        res = super(ResCompany, self).action_archive()  # We archive the company first and only then we decommission.
        for company in self:
            if company.l10n_at_scu_id:
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
                                         company.l10n_at_legal_entity_type: company.l10n_at_legal_entity}})
                api.l10n_at_decommission_scu(company.l10n_at_scu_id)
                company.l10n_at_scu_id = False
        return res
