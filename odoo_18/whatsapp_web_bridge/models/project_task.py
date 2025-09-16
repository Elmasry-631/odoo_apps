from odoo import models

class ProjectTask(models.Model):
    _inherit = ['project.task', 'whatsapp.mixin']
    _name = 'project.task'