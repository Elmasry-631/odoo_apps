from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ReservationConflictWizard(models.TransientModel):
    _name = 'reservation.conflict.wizard'
    _description = 'Reservation Conflict Confirmation'

    trainer_id = fields.Many2one('res.partner', string="Nurse")
    conflict_message = fields.Text(string="Conflict Message")
    flag = fields.Boolean(string='Conflict', default=False)

    def confirm_reservation(self):
        # Confirm and proceed with the active reservation
        active_reservation = self.env['student.admission'].browse(self.env.context.get('active_id'))
        active_reservation.sudo().action_create_reservation_auto_multi()
        active_reservation.state = 'enrolled'
        return {'type': 'ir.actions.act_window_close'}

    def confirm_change_details(self):
        # Confirm and proceed with the active reservation

        reservation_change_wizard = self.env['reservation.change.wizard'].browse(self.env.context.get('active_id'))
        reservation_id = reservation_change_wizard.reservation_id
        reservation_id.write({
            'start_date': reservation_change_wizard.new_start_date,
            'end_date': reservation_change_wizard.new_end_date,
            'trainer_id': reservation_change_wizard.new_trainer_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}

    def cancel_reservation(self):
        # Abort the operation
        return {'type': 'ir.actions.act_window_close'}
