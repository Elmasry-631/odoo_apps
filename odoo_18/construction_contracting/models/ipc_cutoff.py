# models/ipc_cutoff.py
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ConstructionIPC(models.Model):
    _inherit = "construction.ipc"

    is_locked_by_cutoff = fields.Boolean(string="مقفول بعد الإقفال", default=False)

    @api.model
    def _cron_lock_after_cutoff(self):
        first_of_month = date.today().replace(day=1)
        recs = self.sudo().search([('state','=','draft'), ('period_end','<', first_of_month)])
        recs.write({'is_locked_by_cutoff': True})
        return True

    def write(self, vals):
        if any(rec.is_locked_by_cutoff and rec.state == 'draft' for rec in self):
            raise ValidationError(_("تم تجاوز الـCut-off الشهري، لا يمكن التعديل على هذا المستخلص."))
        return super().write(vals)
