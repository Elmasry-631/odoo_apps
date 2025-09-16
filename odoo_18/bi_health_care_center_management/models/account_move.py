from odoo import models, fields, api
from datetime import datetime, timedelta, date


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    student_admission_id = fields.Many2one('student.admission',string='Client Registration')


