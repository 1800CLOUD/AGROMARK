# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    order_sale_id = fields.Many2one('sale.order', 'Orden de Venta', related='sale_line_ids.order_id', readonly=True, store=True, copy=False)

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, 
                                      product=None, partner=None, taxes=None, move_type=None):
        res = super(AccountMoveLine, self)._get_price_total_and_subtotal(price_unit=None, quantity=None, 
                                                                         discount=None, currency=None, 
                                                                         product=None, partner=None, 
                                                                         taxes=None, move_type=None)
        
        return res
    
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(
                price_unit,
                quantity=quantity, 
                currency=currency, 
                product=product, 
                partner=partner, 
                is_refund=move_type in ('out_refund', 'in_refund'))
            total_excluded = taxes_res['total_excluded'] * (1 - (discount / 100.0))
            total_included = total_excluded + (taxes_res['total_included'] - taxes_res['total_excluded'])
            res['price_subtotal'] = total_excluded
            res['price_total'] = total_included
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
    
    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        res = super(AccountMoveLine, self)._get_fields_onchange_subtotal(price_subtotal=None, move_type=None, 
                                                                         currency=None, company=None, date=None)
        return res
    
    def _get_taxes_line_edi(self, dict_tax, tax, rate, type_tax, doc='fe'):
        if doc == 'ds':
            self = self.with_context(tax_base_no_discount=True)
        return super(AccountMoveLine, self)._get_taxes_line_edi(dict_tax, tax, rate, type_tax, doc)
