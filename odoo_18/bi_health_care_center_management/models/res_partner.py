# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import datetime, timedelta, date

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean('Client', readonly=True)
    is_coach = fields.Boolean('Nurse', readonly=True)
    is_driver = fields.Boolean('Driver', readonly=True)
    p_name = fields.Char('Parent Name')
    short_name = fields.Char('Short Name')
    is_disability = fields.Boolean('Disability', default=False)
    disability_description = fields.Text('Disability Description')
    trainer_id = fields.Many2one(string='Current Nurse', comodel_name='res.partner', domain=[('is_coach', '=', True)])
    is_sport = fields.Boolean('Sport Product')
    sport_id = fields.Many2many(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)])
    admission_id = fields.Many2one(comodel_name='student.admission')
    admission_end_date = fields.Date(string='Admission end date', related='admission_id.end_duration')
    is_admission_finished = fields.Boolean()

    birth_date = fields.Date(string='Birth Date', related='admission_id.birth_date')
    level_id = fields.Many2one(string='Level', related='admission_id.c_level_id')
    reservation_ids = fields.One2many(related='admission_id.reservation_ids')
    n_of_reservations = fields.Integer(string='Total reservations', related='admission_id.n_of_reservations')
    n_of_reservations_unfinished = fields.Integer(string='Remaining reservations',
                                                  related='admission_id.n_of_reservations_unfinished', )

    is_warning = fields.Boolean(string="Warning", compute="_compute_is_warning", store=True)

    patient_loc = fields.Char(string="Client Location", help="Enter the Patient Location URL", widget="url")
    nurse_specialty_id = fields.Many2one('nurse.specialty')
    is_nurse_occupied = fields.Boolean(default=False, compute='_compute_is_nurse_occupied', store=1)

    admission_ids = fields.One2many('student.admission', 'confirmed_driver_id', string='Admissions')

    is_driver_occupied = fields.Boolean(default=False, compute='_compute_is_driver_occupied', store=1)

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete="set null")
    is_create_emp = fields.Boolean(string="Create Employee ?")

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)

        # Create an employee automatically when a partner is created
        if vals.get('company_type') == 'person' and vals.get('is_create_emp') == True:
            employee_vals = {
                'name': partner.name,
                'work_email': partner.email,
                'mobile_phone': partner.mobile,
                'work_phone': partner.phone,  # Linking partner as the home address
            }
            employee = self.env['hr.employee'].create(employee_vals)

            # Link employee to partner
            partner.write({'employee_id': employee.id})

        return partner

    @api.depends('admission_ids.state')  # Define correct dependencies
    def _compute_is_driver_occupied(self):
        for record in self:
            driver_admissions = self.env['student.admission'].search([
                ('confirmed_driver_id', '=', record.id),
                ('state', 'in', ['student', 'enrolled'])
            ])
            record.is_driver_occupied = bool(driver_admissions)

    @api.depends('n_of_reservations_unfinished', 'admission_id')
    def _compute_is_nurse_occupied(self):
        for record in self:
            if record.n_of_reservations_unfinished < 1 or record.admission_id == False:
                record.is_nurse_occupied = False
            else:
                record.is_nurse_occupied = True

    @api.depends('n_of_reservations_unfinished', )
    def _compute_is_warning(self):
        for record in self:
            if record.n_of_reservations_unfinished < 2:
                record.is_warning = True
            else:
                record.is_warning = False

    @api.model
    def get_data(self):
        students = self.search([('is_student', '=', True)])
        trainers = self.search([('is_coach', '=', True)])
        inquiries = self.env['student.inquiry'].search([('state', '=', 'new')])
        admissions = self.env['student.admission'].search([])
        enroll_admissions = self.env['student.admission'].search([('state', '=', 'enrolled')])
        bookings = self.env['center.booking'].search([])
        center_spaces = self.env['product.product'].search([('is_space', '=', True)])
        center_event = self.env['event.event'].search([])
        total_sports = self.env['res.partner'].search([('is_sport', '=', True)])
        total_equipment = self.env['product.product'].search([('is_equipment', '=', True)])
        data = {'total_inquiries': len(inquiries), 'total_center_events': len(center_event),
                'total_bookings': len(bookings), 'total_sports': len(total_sports),
                'total_equipment': len(total_equipment), 'total_center_spaces': len(center_spaces),
                'total_trainers': len(trainers), 'total_students': len(students),
                'total_confirm_admissions': len(admissions), 'total_enroll_admissions': len(enroll_admissions)}
        return data

    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        context = self._context
        params = context.get('params')

        if context.get('default_is_student') and not params:
            res.update({
                'is_student': True,
            })
        elif context.get('default_is_student'):
            res.update({
                'is_student': True,
            })
        elif context.get('default_name') and not params:
            res.update({
                'is_student': False,
            })
        elif context.get('default_is_sport') and not params:
            res.update({
                'is_student': False,
            })
        elif context.get('default_is_coach') and not params:
            res.update({
                'is_student': False,
            })
        elif (params and params.get('model') == 'student.admission'):
            res.update({
                'is_student': False,
            })

        return res

    @api.model
    def update_student_admission_state(self):
        """Cron job to update the state of student admission end date."""
        current_date = datetime.now().date()  # Get the current date only (without time)
        students = self.search([])

        for student in students:
            if student.admission_end_date:
                end_date = student.admission_end_date  # Extract the date part of end_date

                if current_date >= end_date:
                    student.is_admission_finished = True
                    student.is_warning = False
