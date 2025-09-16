from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
from pytz import timezone, UTC


class DriverReservation(models.Model):
    _name = "driver.reservation"
    _description = "Client Driver Reservation"
    _order = 'id desc'

    name = fields.Char('Name', compute="_compute_name", store=True, readonly=True)
    ref = fields.Char(string='Reference', related='admission_id.name')
    student_id = fields.Many2one('res.partner', string='Client', required=True,
                                 domain=[('is_student', '=', True)])
    sport_id = fields.Many2one(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)])
    level_id = fields.Many2one('res.partner', string="Health Care Center", domain=[
        ('is_sport', '=', True)])
    trainer_id = fields.Many2one(comodel_name='res.partner', domain=[('is_coach', '=', True)], string='Nurse')
    driver_id = fields.Many2one(comodel_name='res.partner', domain=[('is_driver', '=', True)], string='Driver')

    city_distance_id = fields.Many2one(comodel_name='city.distance', )

    state = fields.Selection([
        ('yet', 'Yet to come'),
        ('today', 'Today'),
        ('finished', 'Finished'), ],
        string='State',
        copy=False, default="yet", store=True)
    is_finished = fields.Boolean()

    check_register = fields.Boolean('Check Register')
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    day_name = fields.Char(string='Day', compute='_compute_day_name', store=True)
    color = fields.Integer()
    admission_id = fields.Many2one('student.admission')
    is_vip = fields.Boolean(string='VIP')
    c_level_id = fields.Many2one('level.level', string='Level', related='admission_id.c_level_id')
    package_id = fields.Many2one('package.package', string='Package', related='admission_id.package_id')
    package_line_id = fields.Many2one('package.package.line', string='Package Info',
                                      related='admission_id.package_line_id')
    student_age = fields.Integer(related='admission_id.age')

    @api.depends('start_date')
    def _compute_day_name(self):
        for record in self:
            if record.start_date:
                # Use strftime to format the date as day name
                record.day_name = record.start_date.strftime('%A')  # e.g., Monday
            else:
                record.day_name = ''

    def action_finish(self):
        for rec in self:
            rec.state = 'finished'

    @api.model
    def update_driver_reservation_states(self):
        """Cron job to update reservation states with correct timezone handling."""
        reservations = self.search([('state', '!=', 'finished')])

        # Get user with ID 2
        user = self.env['res.users'].browse(2)
        user_tz = user.tz or 'UTC'  # Use user's timezone or fallback to UTC
        user_timezone = timezone(user_tz)

        for reservation in reservations:
            if reservation.start_date and reservation.end_date:
                # Get current datetime in UTC and convert to user timezone
                current_datetime_utc = datetime.utcnow().replace(tzinfo=UTC)
                current_datetime_local = current_datetime_utc.astimezone(user_timezone)
                current_date_local = current_datetime_local.date()

                # Convert stored UTC datetime fields to user's local timezone properly
                start_datetime_utc = reservation.start_date  # Assuming this is stored in UTC
                end_datetime_utc = reservation.end_date  # Assuming this is stored in UTC

                end_datetime_local = end_datetime_utc.replace(tzinfo=timezone('UTC')).astimezone(user_timezone)
                start_date_local = start_datetime_utc.replace(tzinfo=timezone('UTC')).astimezone(user_timezone).date()

                # print(f"Checking reservation {reservation.id}:")
                # print(f" - Current Datetime (Local): {current_datetime_local}")
                # print(f" - Start Date (Local): {start_date_local}")
                # print(f" - End Datetime (Local): {end_datetime_local}")
                # print(f" - Comparison Result: {current_datetime_local > end_datetime_local}")

                # Compare only the date for start date logic
                if current_date_local < start_date_local:
                    reservation.state = 'yet'
                elif current_datetime_local >= end_datetime_local:
                    reservation.state = 'finished'
                elif start_date_local == current_date_local:
                    reservation.state = 'today'

    @api.depends('trainer_id', 'driver_id')
    def _compute_name(self):
        for record in self:
            nurse_name = record.trainer_id.name if record.trainer_id.name else "No Nurse"
            driver_name = record.driver_id.name if record.driver_id.name else "No Driver"
            record.name = f"{driver_name} with {nurse_name}"

    def action_change_details(self):
        """Opens the reservation change wizard."""
        self.ensure_one()  # Ensure only one record is selected
        view_id = self.env.ref('bi_health_care_center_management.reservation_driver_change_wizard_form').id
        context = self.env.context.copy()
        context['active_id'] = self.id
        return {
            'name': _('Change Driver Reservation Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reservation.driver.change.wizard',  # Replace with your wizard model name
            'view_id': view_id,
            'context': context,
            'target': 'new',
        }

    # @api.constrains('trainer_id', 'start_date', 'end_date')
    # def _check_trainer_availability(self):
    #     for record in self:
    #         if record.trainer_id and record.start_date and record.end_date:
    #             overlapping_reservations = self.search([
    #                 ('trainer_id', '=', record.trainer_id.id),
    #                 ('id', '!=', record.id),
    #                 ('start_date', '<=', record.end_date),
    #                 ('end_date', '>=', record.start_date)
    #             ])
    #             vip_reservations = overlapping_reservations.filtered(lambda r: r.is_vip)
    #
    #             if vip_reservations:
    #                 # Trigger the confirmation wizard
    #                 self.env['reservation.conflict.wizard'].create({
    #                     'trainer_id': record.trainer_id.id,
    #                     'conflict_message': "There is a VIP reservation in this time. Do you want to proceed?"
    #                 }).with_context(active_id=record.id).action_open_dialog()
    #                 return
    #
    #             if len(overlapping_reservations) >= 5:
    #                 # Trigger the confirmation wizard for capacity
    #                 self.env['reservation.conflict.wizard'].create({
    #                     'trainer_id': record.trainer_id.id,
    #                     'conflict_message': f"Trainer {record.trainer_id.name} already has 5 reservations in this time frame. Do you want to proceed?"
    #                 }).with_context(active_id=record.id).action_open_dialog()
    #                 return

    def unlink(self):
        for record in self:
            if record.state == 'finished':
                raise ValidationError(_("You cannot delete a reservation that is in the 'Finished' state."))
            if record.admission_id.state == 'student':
                raise ValidationError(
                    _("You cannot delete a reservation after creating invoice, but you can still edit your reservation.."))

        return super(DriverReservation, self).unlink()

    #
    # @api.onchange('trainer_id')
    # def _onchange_trainer_id(self):
    #     if self.trainer_id and self.student_id:
    #         self.student_id.trainer_id = self.trainer_id.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(DriverReservation, self).create(vals_list)

        return res
