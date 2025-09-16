from odoo import models, fields, api
from datetime import datetime, timedelta, date
from pytz import timezone, UTC


class DriverReservationChangeWizard(models.TransientModel):
    _name = 'reservation.driver.change.wizard'
    _description = 'Driver Reservation Change Wizard'

    reservation_id = fields.Many2one('student.reservation', string='Reservation', required=True,
                                     default=lambda self: self.env.context.get('active_id'))
    new_start_date = fields.Datetime(string='New Start Date', required=True, )
    new_end_date = fields.Datetime(string='New End Date', required=True, )
    new_driver_id = fields.Many2one('res.partner', domain=[('is_driver', '=', True)], string='New Driver',
                                     required=True, )

    def action_confirm(self):
        reservation = self.env['driver.reservation'].browse(self.reservation_id.id)
        # Convert start_date and end_date from float to datetime
        for record in self:

            if record.new_trainer_id:
                overlapping_reservations = self.env['driver.reservation'].search([
                    ('driver_id', '=', record.new_driver_id.id),
                    ('start_date', '<=', record.new_end_date),
                    ('end_date', '>=', record.new_start_date),
                ])

                vip_reservations = overlapping_reservations.filtered(lambda r: r.is_vip)

                if vip_reservations:
                    # Trigger the confirmation wizard for VIP conflict
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'reservation.driver.conflict.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_driver_id': record.new_driver_id.id,
                            'default_conflict_message': "There is a VIP reservation in this time. Do you want to proceed?",
                            'active_id': record.id,
                            'default_flag': True
                        },
                    }

                if len(overlapping_reservations) >= 1:
                    # Trigger the confirmation wizard for capacity conflict
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'reservation.driver.conflict.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_driver_id': record.new_driver_id.id,
                            'default_conflict_message': f"Driver {record.new_driver_id.name} already has  reservation in this time frame. Do you want to proceed?",
                            'active_id': record.id,
                            'default_flag': True
                        },
                    }

        reservation.write({
            'start_date': self.new_start_date,
            'end_date': self.new_end_date,
            'driver_id': self.new_driver_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
