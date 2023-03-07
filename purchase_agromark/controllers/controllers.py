# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseAgromark(http.Controller):
#     @http.route('/purchase_agromark/purchase_agromark', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_agromark/purchase_agromark/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_agromark.listing', {
#             'root': '/purchase_agromark/purchase_agromark',
#             'objects': http.request.env['purchase_agromark.purchase_agromark'].search([]),
#         })

#     @http.route('/purchase_agromark/purchase_agromark/objects/<model("purchase_agromark.purchase_agromark"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_agromark.object', {
#             'object': obj
#         })
