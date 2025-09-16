# -*- coding: utf-8 -*-
# from odoo import http


# class IeCostemLeadForm(http.Controller):
#     @http.route('/ie_costem_lead_form/ie_costem_lead_form', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ie_costem_lead_form/ie_costem_lead_form/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ie_costem_lead_form.listing', {
#             'root': '/ie_costem_lead_form/ie_costem_lead_form',
#             'objects': http.request.env['ie_costem_lead_form.ie_costem_lead_form'].search([]),
#         })

#     @http.route('/ie_costem_lead_form/ie_costem_lead_form/objects/<model("ie_costem_lead_form.ie_costem_lead_form"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ie_costem_lead_form.object', {
#             'object': obj
#         })

