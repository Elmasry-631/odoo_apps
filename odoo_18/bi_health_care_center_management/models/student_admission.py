# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
from pytz import timezone, UTC

import logging

_logger = logging.getLogger(__name__)


class StudentAdmission(models.Model):
    _name = "student.admission"
    _description = "Client Registrations"
    _order = "id desc"

    weekday_ids = fields.Many2many('weekday', string='Days', default=lambda self: self._get_default_weekdays())

    day_one = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='First Day', )

    day_two = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Second Day', )

    name = fields.Char('Name', required=True,
                       readonly=True, default=lambda self: _('New'))
    student_id = fields.Many2one('res.partner', string='Client Name', required=True,
                                 domain=[('is_coach', '=', False), ('is_driver', '=', False), ('is_sport', '=', False)])
    mobile = fields.Char('Mobile', related='student_id.mobile', store=True, readonly=False)
    p_name = fields.Char('Parent Name', related='student_id.p_name', readonly=False)
    parent_mobile = fields.Char('Parent Mobile', related='student_id.phone', readonly=False)
    p1_name = fields.Char('Parent Name ', related='inquiry_id.p_name', readonly=False)
    parent1_mobile = fields.Char('Parent Mobile ', related='inquiry_id.parent_mobile', readonly=False)
    email = fields.Char('Email', related='student_id.email', store=True, readonly=False)
    is_disability = fields.Boolean(string='Disability', related='student_id.is_disability', store=True, readonly=False)
    disability_description = fields.Text('Disability Description', related='student_id.disability_description',
                                         store=True, readonly=False)
    sport_id = fields.Many2one(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)], )
    level_id = fields.Many2one('res.partner', string="Health Care Center", domain=[('is_sport', '=', True)])
    trainer_id = fields.Many2one(comodel_name='res.partner', domain="[('id','in',trainer_id_domain)]", string='Nurse')
    trainer_id_domain = fields.Many2many('res.partner', compute='_compute_trainer_id_domain')
    driver_id = fields.Many2one(comodel_name='res.partner', domain=[('is_driver', '=', True)], string='Driver')
    confirmed_driver_id = fields.Many2one(comodel_name='res.partner', )
    city_distance_id = fields.Many2one(comodel_name='city.distance', string='To City')
    city_distance_travel_time = fields.Float(related="city_distance_id.travel_time")
    state = fields.Selection([
        ('new', 'New'),
        ('enrolled', 'Submitted'),
        ('student', 'Client'),
        ('cancel', 'Ended')], string='State',
        copy=False, default="new", store=True)
    is_invoiced = fields.Boolean()
    inquiry_id = fields.Many2one('student.inquiry', string='Inquiry')
    check_parent = fields.Boolean('Check Parent', related='inquiry_id.check_parent')
    check_register = fields.Boolean('Check Register')
    start_date = fields.Float(string="Start Date")
    end_date = fields.Float(string="End Date")

    start_duration = fields.Date(string='Start Date', default=lambda self: date.today(), store=1)
    end_duration = fields.Date(string='End Date', compute='_compute_end_duration', store=1)
    duration = fields.Integer("Duration(Days)", compute='_compute_duration')

    is_warning = fields.Boolean(string="Warning", compute="_compute_is_warning", store=True)
    n_of_reservations = fields.Integer(string='Number of reservations', )
    n_of_reservations_done = fields.Integer(string='Number of reservations done',
                                            compute='_compute_n_of_reservations_done')
    n_of_reservations_done_driver = fields.Integer(string='Number of reservations done Driver',
                                                   compute='_compute_n_of_reservations_done_driver')
    reservation_ids = fields.One2many('student.reservation', 'admission_id')
    driver_reservation_ids = fields.One2many('driver.reservation', 'admission_id')
    is_reservation_done = fields.Boolean(defualt=False, compute='_compute_is_reservation_done')
    is_driver_reservation_done = fields.Boolean(defualt=False, compute='_compute_is_driver_reservation_done')
    n_of_reservations_unfinished = fields.Integer(string='UnFinished reservations',
                                                  compute='_compute_n_of_reservations_unfinished', store=1)
    is_vip = fields.Boolean(string='VIP')
    birth_date = fields.Date(string='Birth Date', )
    age = fields.Integer(string='Age', compute='_compute_age')
    c_level_id = fields.Many2one('level.level', string='Level')
    package_id = fields.Many2one('package.package', string='Package')
    package_line_id_domain = fields.Many2many('package.package.line', compute='_compute_package_line_id_domain')
    package_line_id = fields.Many2one('package.package.line', string='Package Details',
                                      domain="[('id', 'in', package_line_id_domain)]")
    is_admission_finished = fields.Boolean()
    nurse_specialty_id = fields.Many2one('nurse.specialty', string='Specialty', required=True, )

    @api.onchange('nurse_specialty_id')
    def _onchange_nurse_specialty_id(self):
        for rec in self:
            rec.trainer_id = False

    @api.depends('nurse_specialty_id', 'start_duration', 'end_duration')
    def _compute_trainer_id_domain(self):
        for rec in self:
            if rec.nurse_specialty_id and rec.start_duration and rec.end_duration:
                # Get all nurses in the specialty
                nurses = rec.nurse_specialty_id.nurse_ids
                available_nurses = []
                
                # Check each nurse's availability
                for nurse in nurses:
                    # Search for overlapping reservations
                    overlapping_reservations = self.env['student.reservation'].search([
                        ('trainer_id', '=', nurse.id),
                        ('state', '!=', 'finished'),
                        '|',
                        '&',
                        ('start_date', '>=', rec.start_duration),
                        ('start_date', '<=', rec.end_duration),
                        '&',
                        ('end_date', '>=', rec.start_duration),
                        ('end_date', '<=', rec.end_duration),
                    ])
                    
                    # If no overlapping reservations found, nurse is available
                    if not overlapping_reservations:
                        available_nurses.append(nurse.id)
                
                rec.trainer_id_domain = available_nurses
            else:
                rec.trainer_id_domain = []

    @api.onchange('start_date', 'package_line_id')
    def _onchange_start_date_package_line_id(self):
        if self.start_date and self.package_line_id:
            self.end_date = self.start_date + self.package_line_id.n_of_hours_peer_session

    @api.model
    def _get_default_weekdays(self):
        return self.env['weekday'].search([]).ids

    @api.depends('package_id')
    def _compute_package_line_id_domain(self):
        for rec in self:
            rec.package_line_id_domain = rec.package_id.line_ids.ids

    @api.onchange('package_line_id', )
    def _onchange_package_line_id(self):
        if self.package_id and self.package_line_id:
            self.n_of_reservations = self.package_line_id.n_of_session

        if self.package_line_id.is_with_friday:
            self.weekday_ids = self.env['weekday'].search([]).ids
        elif not self.package_line_id.is_with_friday:
            self.weekday_ids = self.env['weekday'].search([('name', '!=', 'Friday')]).ids

    @api.onchange('package_id', )
    def _onchange_package_id(self):
        self.package_line_id = False

    @api.depends('start_duration', 'n_of_reservations', 'weekday_ids')
    def _compute_end_duration(self):
        for record in self:
            # Default value assignment
            record.end_duration = False

            # Ensure all required fields are present
            if not record.start_duration or not record.weekday_ids or not record.n_of_reservations:
                _logger.warning("Missing required fields for record ID %s", record.id)
                continue

            try:
                start_date = fields.Date.from_string(record.start_duration)
                weekdays = record.weekday_ids.mapped('name')
                weekday_map = {day: i for i, day in enumerate(
                    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}

                # Filter and sort the selected weekdays
                selected_weekdays = sorted([weekday_map[day] for day in weekdays])
                reservations_left = record.n_of_reservations
                current_date = start_date

                # Calculate the end date
                while reservations_left > 0:
                    if current_date.weekday() in selected_weekdays:
                        reservations_left -= 1
                    current_date += timedelta(days=1)

                # Assign the last reserved date
                record.end_duration = current_date - timedelta(days=1)
            except Exception as e:
                # Log the error for debugging
                _logger.error("Error computing end_duration for record ID %s: %s", record.id, e)
                record.end_duration = False

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = date.today()
                birth_year = record.birth_date.year
                # Calculate age by subtracting birth year from current year and potentially adjusting for incomplete year
                age = today.year - birth_year - (
                        (today.month, today.day) < (record.birth_date.month, record.birth_date.day))
                record.age = age
            else:
                record.age = 0

    @api.depends('reservation_ids.state')
    def _compute_n_of_reservations_unfinished(self):
        for rec in self:
            n_of_unfinished_reservations = len(rec.reservation_ids.filtered(lambda r: r.state != 'finished'))
            rec.n_of_reservations_unfinished = n_of_unfinished_reservations

    @api.depends('reservation_ids')
    def _compute_is_reservation_done(self):
        for rec in self:
            if rec.reservation_ids and len(rec.reservation_ids) == rec.n_of_reservations:
                rec.is_reservation_done = True
            else:
                rec.is_reservation_done = False

    @api.depends('driver_reservation_ids')
    def _compute_is_driver_reservation_done(self):
        for rec in self:
            if rec.driver_reservation_ids and len(rec.driver_reservation_ids) == rec.n_of_reservations * 2:
                rec.is_driver_reservation_done = True
            else:
                rec.is_driver_reservation_done = False

    @api.depends('reservation_ids')
    def _compute_n_of_reservations_done(self):
        for rec in self:
            rec.n_of_reservations_done = len(rec.reservation_ids)

    @api.depends('driver_reservation_ids')
    def _compute_n_of_reservations_done_driver(self):
        for rec in self:
            rec.n_of_reservations_done_driver = len(rec.driver_reservation_ids)

    @api.constrains('n_of_reservations')
    def _check_n_of_reservations(self):
        for record in self:
            if record.n_of_reservations <= 0:
                raise ValidationError("The number of reservations cannot be 0 or negative.")

    @api.constrains('start_date', 'end_date')
    def _check_valid_time(self):

        for record in self:
            try:
                start_time = record.start_date
                end_time = record.end_date
                # Additional Validation: Ensure start_time is before end_time
                if start_time >= end_time:
                    raise ValueError("Start time must be earlier than end time.")
                # Ensure the times are within valid 24-hour format
                if start_time < 0 or end_time < 0:
                    raise ValidationError("Time cannot be negative.")
                if start_time >= 24 or end_time >= 24:
                    raise ValidationError("There is no time beyond 23:59.")

            except ValueError as e:
                raise ValidationError(f"Invalid time format: {e}")

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration <= 0:
                raise ValidationError("The duration cannot be 0 or negative.")

    @api.depends('end_duration')
    def _compute_is_warning(self):
        for record in self:
            if record.end_duration:
                # Calculate the warning date as a `datetime.date`
                warning_date = date.today() + timedelta(days=1)
                # Compare `end_date` (date) with `warning_date` (also date)
                record.is_warning = record.end_duration <= warning_date
            else:
                record.is_warning = False

    @api.model
    def _update_is_warning(self):
        """Update the warning field for all records."""
        admissions = self.search([])
        for admission in admissions:
            admission._compute_is_warning()

    @api.depends('start_duration', 'end_duration')
    def _compute_duration(self):
        for record in self:
            if record.start_duration and record.end_duration:
                # Calculate the number of days directly
                delta = (record.end_duration - record.start_duration).days
                record.duration = float(delta) + 1  # Convert to float if needed
            else:
                record.duration = 0.0

    @api.onchange('trainer_id')
    def _onchange_trainer_id(self):
        if self.trainer_id and self.student_id:
            self.student_id.trainer_id = self.trainer_id.id

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'student.admission') or _('New')

        res = super(StudentAdmission, self).create(vals_list)

        portal_wizard_obj = self.env['portal.wizard']
        for record in res:
            if record.email:  # Ensure email exists
                try:
                    # Attempt to create portal access
                    created_portal_wizard = portal_wizard_obj.create({})
                    portal_wizard_user_obj = self.env['portal.wizard.user']
                    wiz_user_vals = {
                        'wizard_id': created_portal_wizard.id,
                        'partner_id': record.student_id.id,
                        'email': record.student_id.email,
                    }
                    created_portal_wizard_user = portal_wizard_user_obj.create(wiz_user_vals)
                    if created_portal_wizard_user:
                        created_portal_wizard_user.action_grant_access()
                except UserError as e:
                    # Skip granting access if the user already has portal access
                    if 'portal access' in str(e):
                        continue
                    else:
                        raise e  # Re-raise any other errors

        return res

    def action_enroll(self):

        def local_to_utc_naive(dt):
            user_tz = timezone(self.env.user.tz or 'UTC')  # User's timezone
            local_dt = user_tz.localize(dt)  # Localize datetime
            utc_dt = local_dt.astimezone(UTC)  # Convert to UTC
            return utc_dt.replace(tzinfo=None)  # Remove timezone info

        def float_to_datetime(base_date, hour_float):
            """Convert a float hour to a datetime object based on a base date."""
            hour = int(hour_float)
            minute = round((hour_float - hour) * 60)  # Interpret decimal as minutes
            return datetime.combine(base_date, datetime.strptime(f"{hour}:{minute:02}", "%H:%M").time())

        def next_weekday(start_date, weekday):
            """Get the next occurrence of a specific weekday."""
            days_ahead = (weekday - start_date.weekday() + 7) % 7
            return start_date + timedelta(days=days_ahead)

        if not self.weekday_ids or len(self.weekday_ids) < 1:
            raise ValidationError("You must select at least one weekday.")

        start_time = float_to_datetime(self.start_duration, self.start_date).time()
        end_time = float_to_datetime(self.start_duration, self.end_date).time()

        start_day = self.start_duration
        weekday_numbers = sorted([int(weekday.id - 1) for weekday in self.weekday_ids])

        # Generate reservation dates based on selected weekdays
        weekday_schedule = []
        for _ in range(self.n_of_reservations):
            for weekday in weekday_numbers:

                next_date = next_weekday(start_day, weekday)
                weekday_schedule.append(next_date)
            start_day += timedelta(days=7)

        weekday_schedule.sort()


        for record in self:
            if not record.start_duration or not record.end_duration:
                raise ValidationError("Start duration and end duration must be set.")

            for current_date in weekday_schedule[:record.n_of_reservations]:
                start_datetime = datetime.combine(current_date, start_time)
                end_datetime = datetime.combine(current_date, end_time)

                start_datetime_utc = local_to_utc_naive(start_datetime)
                end_datetime_utc = local_to_utc_naive(end_datetime)

                # Calculate driver travel times
                travel_time_minutes = round(record.city_distance_travel_time * 60)  # Convert float to minutes
                travel_time = timedelta(minutes=travel_time_minutes)  # Convert to timedelta

                driver_travel_start_1 = start_datetime - travel_time
                driver_travel_end_1 = start_datetime + travel_time

                driver_travel_start_2 = end_datetime - travel_time
                driver_travel_end_2 = end_datetime + travel_time

                driver_travel_start_1_utc = local_to_utc_naive(driver_travel_start_1)
                driver_travel_end_1_utc = local_to_utc_naive(driver_travel_end_1)

                driver_travel_start_2_utc = local_to_utc_naive(driver_travel_start_2)
                driver_travel_end_2_utc = local_to_utc_naive(driver_travel_end_2)

                # 🚨 Check for trainer conflicts (nurse conflicts)
                if record.trainer_id:
                    overlapping_reservations = self.env['student.reservation'].search([
                        ('trainer_id', '=', record.trainer_id.id),
                        ('start_date', '<=', end_datetime_utc),
                        ('end_date', '>=', start_datetime_utc),
                        ('state', '!=', 'finished'),

                    ])

                    if overlapping_reservations:
                        raise ValidationError(
                            f"Nurse {record.trainer_id.name} has an existing reservation on {current_date}.")

                # 🚨 Check for driver conflicts across selected weekdays
                if record.driver_id:
                    # Step 1: Check for conflicting reservations with a DIFFERENT `city_distance_id`
                    overlapping_driver_reservations_not_same_distance = self.env['driver.reservation'].search([
                        ('driver_id', '=', record.driver_id.id),
                        ('city_distance_id', '!=', record.city_distance_id.id),
                        ('state', '!=', 'finished'),
                        '|',
                        '&',  # First travel time range check
                        ('start_date', '<=', driver_travel_end_1_utc),
                        ('end_date', '>=', driver_travel_start_1_utc),
                        '&',  # Second travel time range check
                        ('start_date', '<=', driver_travel_end_2_utc),
                        ('end_date', '>=', driver_travel_start_2_utc),
                    ])

                    if overlapping_driver_reservations_not_same_distance:
                        raise ValidationError(
                            f"Driver {record.driver_id.name} has a conflicting reservation for a different distance on {current_date}. Enrollment cannot proceed.")

                    # Step 2: Check for overlapping reservations with the SAME `city_distance_id`
                    overlapping_driver_reservations_same_distance = self.env['driver.reservation'].search([
                        ('driver_id', '=', record.driver_id.id),
                        ('city_distance_id', '=', record.city_distance_id.id),
                        ('state', '!=', 'finished'),
                        '|',
                        '&',  # First travel time range check
                        ('start_date', '<=', driver_travel_end_1_utc),
                        ('end_date', '>=', driver_travel_start_1_utc),
                        '&',  # Second travel time range check
                        ('start_date', '<=', driver_travel_end_2_utc),
                        ('end_date', '>=', driver_travel_start_2_utc),
                    ])

                    # Count distinct nurses in overlapping reservations
                    unique_nurses = set(overlapping_driver_reservations_same_distance.mapped('trainer_id.id'))

                    if len(unique_nurses) >= 3:
                        raise ValidationError(
                            f"Driver {record.driver_id.name} already has 3 nurses assigned for a trip on {current_date}. No more nurses can be added.")

                    if overlapping_driver_reservations_same_distance:
                        return {
                            'type': 'ir.actions.act_window',
                            'res_model': 'reservation.conflict.wizard',
                            'view_mode': 'form',
                            'target': 'new',
                            'context': {
                                'default_driver_id': record.driver_id.id,
                                'default_conflict_message': f"Driver {record.driver_id.name} has {len(unique_nurses)} nurses already assigned for a trip on {current_date}. Do you want to proceed?",
                                'active_id': record.id,
                            },
                        }

        # If no conflicts, proceed with reservation creation
        self.action_create_reservation_auto_multi()

        # Send enrollment email
        template = self.env.ref('bi_health_care_center_management.student_admission_enroll_email_template')
        if template:
            template.send_mail(self.id, force_send=True)

    def action_make_student(self):
        if not self.is_invoiced:
            return {
                'name': 'Create Invoice',
                'view_mode': 'form',
                'res_model': 'create.invoice',
                'type': 'ir.actions.act_window',
                'context': self._context,
                'target': 'new',
            }
        if self.is_invoiced:
            self.state = 'student'
            self.student_id.update({'is_student': True})

    def action_cancel(self):
        self.ensure_one()

        # Cancel any linked invoices
        invoice_ids = self.env['account.move'].search([('invoice_origin', '=', self.name)])
        if len(invoice_ids.ids) == 1:
            invoice = invoice_ids
            invoice.button_cancel()

        # Update state to 'cancel'
        self.state = 'cancel'

        # Remove student status
        self.student_id.update({'is_student': False})

        # Remove trainer admission link
        self.trainer_id.update({'admission_id': False})

        # Remove admission reference from driver
        if self.confirmed_driver_id:
            self.confirmed_driver_id = False

        # Delete unfinished reservations
        for reserv in self.reservation_ids:
            if reserv.state != 'finished':
                reserv.unlink()

        for d_reserv in self.driver_reservation_ids:
            if d_reserv.state != 'finished':
                d_reserv.unlink()

    def action_cancel_cron(self):
        current_date = datetime.now().date()
        admissions = self.search([('end_duration', '!=', False)])

        for admission in admissions:
            if admission.end_duration and current_date >= admission.end_duration:
                # Mark admission as finished and cancel it
                admission.is_admission_finished = True
                admission.state = 'cancel'

                # Update student and trainer records
                admission.student_id.update({'is_student': False})
                admission.trainer_id.update({'admission_id': False})

                # Remove the admission from the driver's admission list
                if admission.driver_id:
                    admission.confirmed_driver_id = False

    def action_new(self):
        self.ensure_one()
        self.state = 'new'

    def action_view_invoice(self):
        self.ensure_one()
        invoice_ids = self.env['account.move'].search([('invoice_origin', '=', self.name)])
        if invoice_ids:
            action = {
                'name': _("Admission Invoices"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'target': 'current',
            }
            if len(invoice_ids.ids) == 1:
                invoice = invoice_ids.ids[0]
                action['res_id'] = invoice
                action['view_mode'] = 'form'
                action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            else:
                action['view_mode'] = 'list,form'
                action['domain'] = [('id', 'in', invoice_ids.ids)]
            return action

    def action_create_reservation(self):
        """Open a new form view for creating a reservation."""
        self.ensure_one()  # Ensure the action is executed on a single record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Reservation',
            'res_model': 'student.reservation',
            'view_mode': 'form',
            'view_id': self.env.ref('bi_health_care_center_management.student_reservation_view_form').id,
            'target': 'new',  # Open in dialog (new form)
            'context': {
                'default_student_id': self.student_id.id,  # Pre-fill student
                'default_admission_id': self.id,  # Link to current admission
                'default_trainer_id': self.trainer_id.id,  # Link to current admission
                'default_sport_id': self.sport_id.id,  # Link to current admission
                'default_level_id': self.level_id.id,  # Link to current admission
            }
        }

    def action_create_driver_reservation(self):
        """Open a new form view for creating a reservation."""
        self.ensure_one()  # Ensure the action is executed on a single record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Driver Reservation',
            'res_model': 'driver.reservation',
            'view_mode': 'form',
            'view_id': self.env.ref('bi_health_care_center_management.driver_reservation_view_form').id,
            'target': 'new',  # Open in dialog (new form)
            'context': {
                'default_student_id': self.student_id.id,  # Pre-fill student
                'default_admission_id': self.id,  # Link to current admission
                'default_trainer_id': self.trainer_id.id,  # Link to current admission
                'default_driver_id': self.driver_id.id,  # Link to current admission
                'default_sport_id': self.sport_id.id,  # Link to current admission
                'default_level_id': self.level_id.id,  # Link to current admission
            }
        }

    def action_create_reservation_auto(self):
        self.ensure_one()

        # Ensure days are different
        if self.day_one == self.day_two:
            raise ValidationError("The two selected days must be different.")

        # Convert float time to datetime.time
        def float_to_time(hour_float):
            hour = int(hour_float)
            minute = round((hour_float - hour) * 100)  # Avoid precision issues
            if minute >= 60:
                raise ValueError("Invalid time format: Minutes cannot exceed 59.")
            return datetime.strptime(f"{hour}:{minute:02}", "%H:%M").time()

        # Calculate the next occurrence of a given weekday
        def next_weekday(current_date, weekday):
            days_ahead = (weekday - current_date.weekday() + 7) % 7
            return current_date + timedelta(days=days_ahead)

        # Convert to UTC and make datetime naive
        def local_to_utc_naive(dt):
            user_tz = timezone(self.env.user.tz or 'UTC')  # User's timezone
            local_dt = user_tz.localize(dt)  # Localize datetime
            utc_dt = local_dt.astimezone(UTC)  # Convert to UTC
            return utc_dt.replace(tzinfo=None)  # Remove timezone info

        start_time = float_to_time(self.start_date)
        end_time = float_to_time(self.end_date)
        today = datetime.now().date()

        # Get first occurrences of the selected days
        day_one_date = next_weekday(today, int(self.day_one))
        day_two_date = next_weekday(today, int(self.day_two))

        # Ensure the starting day is the closest to today
        if day_one_date <= day_two_date:
            next_dates = [day_one_date, day_two_date]
        else:
            next_dates = [day_two_date, day_one_date]

        reservations = []

        # Generate reservations
        for i in range(self.n_of_reservations):
            # Get the next date in the cycle
            current_date = next_dates[i % 2]  # Alternates between day_one and day_two

            # Ensure the next date always advances
            next_dates[i % 2] += timedelta(days=7)

            start_datetime = datetime.combine(current_date, start_time)
            end_datetime = datetime.combine(current_date, end_time)

            # Convert to UTC and make naive
            start_datetime_utc = local_to_utc_naive(start_datetime)
            end_datetime_utc = local_to_utc_naive(end_datetime)

            reservations.append({
                'student_id': self.student_id.id,
                'admission_id': self.id,
                'trainer_id': self.trainer_id.id,
                'sport_id': self.sport_id.id,
                'level_id': self.level_id.id,
                'start_date': start_datetime_utc,
                'end_date': end_datetime_utc,
                'is_vip': self.is_vip
            })

        # Batch create reservations
        self.env['student.reservation'].create(reservations)

    def action_create_reservation_auto_multi(self):
        self.ensure_one()

        if not self.weekday_ids or len(self.weekday_ids) < 1:
            raise ValidationError("You must select at least one weekday.")

        # Convert float to datetime.time
        def float_to_time(hour_float):
            hour = int(hour_float)
            minute = round((hour_float - hour) * 60)
            return datetime.strptime(f"{hour}:{minute:02}", "%H:%M").time()

        # Get the next occurrence of a weekday from today
        def next_weekday(current_date, weekday):
            days_ahead = (weekday - current_date.weekday() + 7) % 7
            return current_date + timedelta(days=days_ahead)

        # Convert to UTC and remove timezone info
        def local_to_utc_naive(dt):
            user_tz = timezone(self.env.user.tz or 'UTC')
            local_dt = user_tz.localize(dt)
            utc_dt = local_dt.astimezone(UTC)
            return utc_dt.replace(tzinfo=None)

        # Convert start and end times
        start_time = float_to_time(self.start_date)
        end_time = float_to_time(self.end_date)

        start_day = self.start_duration

        # Get all future occurrences of selected weekdays in a list
        weekday_numbers = sorted([int(weekday.id - 1) for weekday in self.weekday_ids])

        # Prepare a queue of dates for selected weekdays
        weekday_schedule = []
        for _ in range(self.n_of_reservations):
            for weekday in weekday_numbers:
                next_date = next_weekday(start_day, weekday)
                weekday_schedule.append(next_date)
            start_day += timedelta(days=7)  # Move to next week

        # Sort schedule to maintain chronological order
        weekday_schedule.sort()

        reservations = []
        driver_reservations = []

        # Convert city travel time to minutes
        travel_time_minutes = round(self.city_distance_travel_time * 60)  # Convert float (hours) to minutes
        travel_time = timedelta(minutes=travel_time_minutes)  # Convert to timedelta

        # Generate reservations using the precomputed schedule
        for i in range(self.n_of_reservations):
            current_date = weekday_schedule[i]

            start_datetime = datetime.combine(current_date, start_time)
            end_datetime = datetime.combine(current_date, end_time)

            start_datetime_utc = local_to_utc_naive(start_datetime)
            end_datetime_utc = local_to_utc_naive(end_datetime)

            # Create the normal reservation
            reservations.append({
                'student_id': self.student_id.id,
                'admission_id': self.id,
                'trainer_id': self.trainer_id.id,
                'start_date': start_datetime_utc,
                'end_date': end_datetime_utc,
            })

            # Create the first driver reservation (before start_date)
            driver_start_datetime = start_datetime - travel_time
            driver_end_datetime = start_datetime + travel_time

            driver_reservations.append({
                'driver_id': self.driver_id.id,  # Assuming the driver is stored in self.driver_id
                'student_id': self.student_id.id,
                'admission_id': self.id,
                'trainer_id': self.trainer_id.id,
                'city_distance_id': self.city_distance_id.id,
                'start_date': local_to_utc_naive(driver_start_datetime),
                'end_date': local_to_utc_naive(driver_end_datetime),
            })

            # Create the second driver reservation (before end_date)
            driver_start_datetime_2 = end_datetime - travel_time
            driver_end_datetime_2 = end_datetime + travel_time

            driver_reservations.append({
                'driver_id': self.driver_id.id,
                'student_id': self.student_id.id,
                'admission_id': self.id,
                'trainer_id': self.trainer_id.id,
                'city_distance_id': self.city_distance_id.id,
                'start_date': local_to_utc_naive(driver_start_datetime_2),
                'end_date': local_to_utc_naive(driver_end_datetime_2),
            })

        # Batch create reservations
        self.env['student.reservation'].create(reservations)
        self.env['driver.reservation'].create(driver_reservations)

        self.state = 'enrolled'
        self.student_id.admission_id = self.id
        self.trainer_id.admission_id = self.id
        self.confirmed_driver_id = self.driver_id.id

    def action_view_reservations(self):
        self.ensure_one()
        reservation_ids = self.env['student.reservation'].search([('ref', '=', self.name)])
        if reservation_ids:
            action = {'name': _("Client Reservations"),
                      'type': 'ir.actions.act_window',
                      'res_model': 'student.reservation',
                      'target': 'current', 'view_mode': 'list,form,calendar',
                      'domain': [('id', 'in', reservation_ids.ids)]}
            return action

    def action_view_reservations_driver(self):
        self.ensure_one()
        driver_reservation_ids = self.env['driver.reservation'].search([('ref', '=', self.name)])
        if driver_reservation_ids:
            action = {'name': _("Driver Reservations"),
                      'type': 'ir.actions.act_window',
                      'res_model': 'driver.reservation',
                      'target': 'current', 'view_mode': 'list,form,calendar',
                      'domain': [('id', 'in', driver_reservation_ids.ids)]}
            return action

    def unlink(self):
        for record in self:
            if record.state in ['student', 'enrolled', 'cancel']:
                raise ValidationError(
                    _("You cannot delete an admission after its enrollment."))
        return super(StudentAdmission, self).unlink()
