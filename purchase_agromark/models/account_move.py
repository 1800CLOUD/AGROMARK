# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', 'Orden de Venta', related='invoice_line_ids.sale_line_ids.order_id', readonly=True, store=True, copy=False)

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        if self.move_type in ('in_invoice', 'in_refund'):
            self = self.with_context(tax_base_no_discount=True)
        return super(AccountMove, self)._recompute_tax_lines(recompute_tax_base_amount, tax_rep_lines_to_recompute)