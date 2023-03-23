# -*- coding: utf-8 -*-
# from odoo import http


# class HelpdeskSmachine(http.Controller):
#     @http.route('/helpdesk_smachine/helpdesk_smachine', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpdesk_smachine/helpdesk_smachine/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpdesk_smachine.listing', {
#             'root': '/helpdesk_smachine/helpdesk_smachine',
#             'objects': http.request.env['helpdesk_smachine.helpdesk_smachine'].search([]),
#         })

#     @http.route('/helpdesk_smachine/helpdesk_smachine/objects/<model("helpdesk_smachine.helpdesk_smachine"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpdesk_smachine.object', {
#             'object': obj
#         })
