# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class NurseSpecialty(models.Model):
    _name = 'nurse.specialty'
    _description = 'Nurse Specialty'
    _order = 'id desc'

    name = fields.Char(string='Name', required=1)
    description = fields.Text(string='Description')
    nurse_ids = fields.One2many('res.partner','nurse_specialty_id',domain=[('is_coach', '=', True)],string='Nurses')
    # line_ids = fields.One2many('package.package.line', 'package_id')


# class PackageLine(models.Model):
#     _name = 'package.package.line'
#     _description = 'Packages Lines'
#
#     name = fields.Char(string='Name', compute='_compute_name', store=True)
#     package_id = fields.Many2one('package.package')
#     n_of_session = fields.Integer(string='Number of Days', required=1)
#     price = fields.Float(string="Price", required=1)
#     product_id = fields.Many2one('product.template', string="Product", required=1)
#
#     @api.onchange('price')
#     def _onchange_price(self):
#         if self.product_id:
#             self.product_id.list_price = self.price
#
#     @api.depends('product_id')
#     def _compute_name(self):
#         for record in self:
#             record.name = record.product_id.name if record.product_id else ''
