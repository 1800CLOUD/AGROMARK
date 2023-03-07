# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals['price_unit'] = self.price_unit
        return vals
    
    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        res = super(PurchaseOrderLine, self)._compute_amount()
        for line in self:
            taxes = line.taxes_id.compute_all(**line._prepare_compute_all_values())
            total_excluded = taxes['total_excluded'] * (1 - line.discount / 100)
            total_tax = taxes['total_included'] - taxes['total_excluded']
            total_included = total_excluded + total_tax
            line.update({
                'price_tax': total_tax,
                'price_total': total_included,
                'price_subtotal': total_excluded,
            })
        return res