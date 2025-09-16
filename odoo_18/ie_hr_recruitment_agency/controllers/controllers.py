# -*- coding: utf-8 -*-
# from odoo import http


# class IeHrRecruitmentAgency(http.Controller):
#     @http.route('/ie_hr_recruitment_agency/ie_hr_recruitment_agency', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ie_hr_recruitment_agency/ie_hr_recruitment_agency/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ie_hr_recruitment_agency.listing', {
#             'root': '/ie_hr_recruitment_agency/ie_hr_recruitment_agency',
#             'objects': http.request.env['ie_hr_recruitment_agency.ie_hr_recruitment_agency'].search([]),
#         })

#     @http.route('/ie_hr_recruitment_agency/ie_hr_recruitment_agency/objects/<model("ie_hr_recruitment_agency.ie_hr_recruitment_agency"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ie_hr_recruitment_agency.object', {
#             'object': obj
#         })

