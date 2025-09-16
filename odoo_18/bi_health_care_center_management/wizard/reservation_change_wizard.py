from odoo import models, fields, api
from datetime import datetime, timedelta, date
from pytz import timezone, UTC


class ReservationChangeWizard(models.TransientModel):
    _name = 'reservation.change.wizard'
    _description = 'Reservation Change Wizard'

    reservation_id = fields.Many2one('student.reservation', string='Reservation', required=True,
                                     default=lambda self: self.env.context.get('active_id'))
    new_start_date = fields.Datetime(string='New Start Date', required=True, )
    new_end_date = fields.Datetime(string='New End Date', required=True, )
    new_trainer_id = fields.Many2one('res.partner', domain=[('is_coach', '=', True)], string='New Nurse',
                                     required=True, )

    def action_confirm(self):
        reservation = self.env['student.reservation'].browse(self.reservation_id.id)
        # Convert start_date and end_date from float to datetime
        for record in self:

            if record.new_trainer_id:
                overlapping_reservations = self.env['student.reservation'].search([
                    ('trainer_id', '=', record.new_trainer_id.id),
                    ('start_date', '<=', record.new_end_date),
                    ('end_date', '>=', record.new_start_date),
                ])

                vip_reservations = overlapping_reservations.filtered(lambda r: r.is_vip)

                if vip_reservations:
                    # Trigger the confirmation wizard for VIP conflict
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'reservation.conflict.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_trainer_id': record.new_trainer_id.id,
                            'default_conflict_message': "There is a VIP reservation in this time. Do you want to proceed?",
                            'active_id': record.id,
                            'default_flag': True
                        },
                    }

                if len(overlapping_reservations) >= 1:
                    # Trigger the confirmation wizard for capacity conflict
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'reservation.conflict.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_trainer_id': record.new_trainer_id.id,
                            'default_conflict_message': f"Nurse {record.new_trainer_id.name} already has 1 reservation in this time frame. Do you want to proceed?",
                            'active_id': record.id,
                            'default_flag': True
                        },
                    }

        reservation.write({
            'start_date': self.new_start_date,
            'end_date': self.new_end_date,
            'trainer_id': self.new_trainer_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
