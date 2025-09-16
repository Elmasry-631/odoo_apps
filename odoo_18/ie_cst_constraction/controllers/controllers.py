# -*- coding: utf-8 -*-
# from odoo import http


# class IeCstConstraction(http.Controller):
#     @http.route('/ie_cst_constraction/ie_cst_constraction', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ie_cst_constraction/ie_cst_constraction/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ie_cst_constraction.listing', {
#             'root': '/ie_cst_constraction/ie_cst_constraction',
#             'objects': http.request.env['ie_cst_constraction.ie_cst_constraction'].search([]),
#         })

#     @http.route('/ie_cst_constraction/ie_cst_constraction/objects/<model("ie_cst_constraction.ie_cst_constraction"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ie_cst_constraction.object', {
#             'object': obj
#         })

