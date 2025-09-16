from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ContractAmendWizard(models.TransientModel):
    _name = "contract.amend.wizard"
    _description = "Amend Contract Terms"

    contract_id = fields.Many2one("construction.contract", required=True)
    retention_rate = fields.Float(string="Retention %")
    advance_percent = fields.Float(string="Advance %")
    advance_recovery_ipcs = fields.Integer(string="IPC Count for Advance Recovery")
    ld_rate_per_day = fields.Float(string="LD Rate/Day %")
    ld_cap_percent = fields.Float(string="LD Cap %")

    def action_apply(self):
        self.ensure_one()
        c = self.contract_id
        c.write({
            "retention_rate": self.retention_rate,
            "advance_percent": self.advance_percent,
            "advance_recovery_ipcs": self.advance_recovery_ipcs,
            "ld_rate_per_day": self.ld_rate_per_day,
            "ld_cap_percent": self.ld_cap_percent,
        })
        # يفضَّل ربطه بموافقة داخلية/Activity
        return {"type": "ir.actions.act_window_close"}
