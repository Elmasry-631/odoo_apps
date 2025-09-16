from odoo import models, fields

class NurseReservationReportWizard(models.TransientModel):
    _name = 'nurse.reservation.report.wizard'
    _description = 'Nurse Reservation Report Wizard'

    trainer_id = fields.Many2one('res.partner', string='Nurse', domain=[('is_coach', '=', True)])
    date_from = fields.Datetime(string='Start Date')
    date_to = fields.Datetime(string='End Date')

    def action_print_report(self):
        domain = []
        if self.trainer_id:
            domain.append(('trainer_id', '=', self.trainer_id.id))
        if self.date_from:
            domain.append(('start_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('end_date', '<=', self.date_to))

        reservations = self.env['student.reservation'].search(domain)

        return self.env.ref('bi_health_care_center_management.report_student_reservation_pdf').report_action(reservations)
