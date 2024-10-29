from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_at_fon_participant = fields.Char(related='company_id.l10n_at_fon_participant', string='FON Participant',
                                          readonly=False)
    l10n_at_fon_user_id = fields.Char(related='company_id.l10n_at_fon_user_id', string='FON User ID', readonly=False)
    l10n_at_fon_pin = fields.Char(related='company_id.l10n_at_fon_pin', string='FON PIN', readonly=False)
    l10n_at_legal_entity_type = fields.Selection(related='company_id.l10n_at_legal_entity_type',
                                                 string='Legal Entity Type', readonly=False)
    l10n_at_legal_entity = fields.Char(related='company_id.l10n_at_legal_entity', string='Legal Entity Number',
                                       readonly=False)
    l10n_at_scu_id = fields.Char(related='company_id.l10n_at_scu_id', string='Fiskaly SCU ID', readonly=True)
    l10_at_is_country_austria = fields.Boolean(related='company_id.is_country_austria',
                                               string='Company located in Austria', readonly=True)
    pos_l10n_at_create_cash_register = fields.Boolean(related="pos_config_id.l10n_at_create_cash_register",
                                                      string="Create Cash Register", readonly=False)
    pos_l10n_at_cash_register_id = fields.Char(related="pos_config_id.l10n_at_cash_register_id")
