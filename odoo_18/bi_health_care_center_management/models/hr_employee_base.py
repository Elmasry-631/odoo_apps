
from odoo import _, api, fields, models



class HrEmployeeBaseInherit(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _create_work_contacts(self):
        pass
