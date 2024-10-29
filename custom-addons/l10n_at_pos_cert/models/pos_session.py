from odoo import models, fields, api
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    l10n_at_cash_register_id = fields.Char(related='config_id.l10n_at_cash_register_id', readonly=True)
    l10n_at_cash_register_state = fields.Selection(related='config_id.l10n_at_cash_register_state', readonly=True)

    def action_pos_session_open(self):
        res = super(PosSession, self).action_pos_session_open()

        if res:
            for session in self:
                if not session.config_id.l10n_at_cash_register_id:
                    continue
                session.config_id.action_check_for_outage() # Check if the cash register is in a valid state.
                if session.l10n_at_cash_register_state in ['OUTAGE', 'DECOMMISSIONED', 'DEFECTIVE']:

                    raise UserError(f'Cash Register is in invalid state: {session.l10n_at_cash_register_state}')

                if session.l10n_at_cash_register_state == 'CREATED':
                    session.config_id.action_update_cash_register_state('REGISTERED')

                if session.l10n_at_cash_register_state == 'REGISTERED':
                    session.config_id.action_update_cash_register_state('INITIALIZED')

                session.config_id.action_list_all_cash_registers()
                session.config_id.action_retrieve_and_update_metadata_cash_register()

        return res
