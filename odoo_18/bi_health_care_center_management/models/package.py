# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class Package(models.Model):
    _name = 'package.package'
    _description = 'Packages'

    name = fields.Char(string='Name', required=1)
    description = fields.Text(string='Description')
    line_ids = fields.One2many('package.package.line', 'package_id')


class PackageLine(models.Model):
    _name = 'package.package.line'
    _description = 'Packages Lines'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    package_id = fields.Many2one('package.package')
    n_of_session = fields.Integer(string='Days', required=1)
    n_of_hours_peer_session = fields.Integer(string='Hours', required=1)
    is_with_friday = fields.Boolean(string='With Friday')
    price = fields.Float(string="Price", required=1)
    product_id = fields.Many2one('product.template', string="Product", required=1)

    @api.constrains('n_of_session', 'n_of_hours_peer_session')
    def check_invalid_session_numbers(self):
        if self.n_of_session < 1:
            raise ValidationError(
                _('Number of days cant be 0 or negative !!'))

        if self.n_of_hours_peer_session < 1:
            raise ValidationError(
                _('Number of hours cant be 0 or negative !!'))

    @api.constrains('price')
    def check_invalid_price(self):
        if self.price < 1:
            raise ValidationError(
                _('Price cant be 0 or negative !!'))

    @api.onchange('price')
    def _onchange_price(self):
        if self.product_id:
            self.product_id.list_price = self.price

    @api.depends('product_id')
    def _compute_name(self):
        for record in self:
            record.name = record.product_id.name if record.product_id else ''
