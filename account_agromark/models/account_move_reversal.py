# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    date_mode = fields.Selection(selection='_get_selection_date_mode', required=True, default='custom')
# ('entry', 'Journal Entry Date')

    @api.model
    def _get_selection_date_mode(self):
        return [('custom', _('Specific')),]
