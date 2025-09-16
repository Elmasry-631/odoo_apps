from odoo import fields, models

class Estimate(models.Model):
    _name = "ie.cst.estimate"
    _description = "Project Construction Estimate"

    item = fields.Char()
    activity = fields.Char()
    # material = fields.Many2many("product.product", string="Materials")
    # equipment = fields.Many2many("product.product", string="Equipment")
    # employee_name = fields.Many2many("hr.employee", string="Employees")
    # progress = fields.Many2one("project.task.type", string="Progress Stage")

    dependence = fields.Char()
    plan_time = fields.Datetime()
    begin_in = fields.Datetime()
    end_in = fields.Datetime()
    dependence2 = fields.Char()
    subcontractor = fields.Many2one("res.partner", string="Subcontractor")
