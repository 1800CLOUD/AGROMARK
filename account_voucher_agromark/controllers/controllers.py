# -*- coding: utf-8 -*-
# from odoo import http


# class AccountVoucherAgromark(http.Controller):
#     @http.route('/account_voucher_agromark/account_voucher_agromark', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_voucher_agromark/account_voucher_agromark/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_voucher_agromark.listing', {
#             'root': '/account_voucher_agromark/account_voucher_agromark',
#             'objects': http.request.env['account_voucher_agromark.account_voucher_agromark'].search([]),
#         })

#     @http.route('/account_voucher_agromark/account_voucher_agromark/objects/<model("account_voucher_agromark.account_voucher_agromark"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_voucher_agromark.object', {
#             'object': obj
#         })
