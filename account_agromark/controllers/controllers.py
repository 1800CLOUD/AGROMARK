# -*- coding: utf-8 -*-
# from odoo import http


# class AccountAgromark(http.Controller):
#     @http.route('/account_agromark/account_agromark', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_agromark/account_agromark/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_agromark.listing', {
#             'root': '/account_agromark/account_agromark',
#             'objects': http.request.env['account_agromark.account_agromark'].search([]),
#         })

#     @http.route('/account_agromark/account_agromark/objects/<model("account_agromark.account_agromark"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_agromark.object', {
#             'object': obj
#         })
