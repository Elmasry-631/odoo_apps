# -*- coding: utf-8 -*-
# from odoo import http


# class IeEquipmentRental(http.Controller):
#     @http.route('/ie_equipment_rental/ie_equipment_rental', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ie_equipment_rental/ie_equipment_rental/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ie_equipment_rental.listing', {
#             'root': '/ie_equipment_rental/ie_equipment_rental',
#             'objects': http.request.env['ie_equipment_rental.ie_equipment_rental'].search([]),
#         })

#     @http.route('/ie_equipment_rental/ie_equipment_rental/objects/<model("ie_equipment_rental.ie_equipment_rental"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ie_equipment_rental.object', {
#             'object': obj
#         })

