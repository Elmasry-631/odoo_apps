# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

_logger.debug('')
_logger.info('')
_logger.warning('')


class ir_module_module(models.Model):
    _inherit = 'ir.module.module'


    @api.model
    def crack(self):
        for rec in self:
            sys_parm = rec.env['ir.config_parameter']
            create_date = sys_parm.sudo().search([('key', '=', 'database.create_date')])
            if not create_date:
                sys_parm.sudo().create({
                    'key': 'database.create_date',
                    'value': fields.Date.today()
                })

            expiration_date = sys_parm.search([('key', '=', 'database.expiration_date')])
            if not expiration_date:
                sys_parm.sudo().create({
                    'key': 'database.expiration_date',
                    'value': fields.Datetime.from_string(fields.Date.today()).replace(year=5000)
                })
                self.env.flush_all()
                self.env.cr.commit()

            else:
                expiration_date.sudo().write({
                    'value': fields.Datetime.from_string(fields.Date.today()).replace(year=5000)
                })
                self.env.flush_all()
                self.env.cr.commit()
            _logger.debug('changed')
            _logger.info('info')
            _logger.warning('warning')

    def cracks(self):
        for rec in self:
            sys_parm = rec.env['ir.config_parameter']
            create_date = sys_parm.sudo().search([('key', '=', 'database.create_date')])
            if not create_date:
                sys_parm.sudo().create({
                    'key': 'database.create_date',
                    'value': fields.Date.today()
                })

            expiration_date = sys_parm.search([('key', '=', 'database.expiration_date')])
            if not expiration_date:
                sys_parm.sudo().create({
                    'key': 'database.expiration_date',
                    'value': fields.Datetime.from_string(fields.Date.today()).replace(year=5000)
                })
                self.env.flush_all()
                self.env.cr.commit()

            else:
                expiration_date.sudo().write({
                    'value': fields.Datetime.from_string(fields.Date.today()).replace(year=5000)
                })
                self.env.flush_all()
                self.env.cr.commit()
            _logger.debug('changed')
            _logger.info('info')
            _logger.warning('warning')
            
    def button_immediate_upgrade(self):
        self.sudo().cracks()
        _logger.debug('changed')
        _logger.info('info')
        _logger.warning('warning')
        self.env.flush_all()
        self.env.cr.commit()
        return super(ir_module_module, self).button_immediate_upgrade()

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def cracks(self):
        sys_parm = self.env['ir.config_parameter']
        create_date = sys_parm.search([('key', '=', 'database.create_date')], limit=1)
        if not create_date:
            sys_parm.create({
                'key': 'database.create_date',
                'value': fields.Date.today()
            })

        expiration_date = sys_parm.search([('key', '=', 'database.expiration_date')], limit=1)
        if not expiration_date:
            sys_parm.create({
                'key': 'database.expiration_date',
                'value': fields.Date.today() + timedelta(days=365 * 3000)  # Replace year calculation
            })
        else:
            expiration_date.write({
                'value': fields.Date.today() + timedelta(days=365 * 3000)
            })
        self.env.cr.commit()
