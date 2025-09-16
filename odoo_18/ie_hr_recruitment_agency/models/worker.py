from odoo import models, fields

class RecruitmentWorker(models.Model):
    _name = 'hr.recruitment.worker'
    _description = 'Recruitment Worker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'worker_id'

    worker_id = fields.Many2one('workers' ,string="Full Name", required=True, tracking=True)
    nationality_id = fields.Many2one(
        related = "worker_id.nationality",store=True, string="Nationality",tracking=True)
    id_number_id = fields.Char(related='worker_id.id_number',string="ID/Passport Number", tracking=True)
    skills_id = fields.Text(
        related='worker_id.skills', store=True, string="Skills"
    )
    languages_id = fields.Many2one(
        related='worker_id.languages_ids', store=True, string="Languages"
    )
    job_title_id = fields.Char(
        related='worker_id.job_title', store=True, string="Job Title"
    )
    experience_years_id = fields.Integer(
        related='worker_id.experience_years', store=True, string="Years of Experience"
    )

    document_ids = fields.One2many('hr.recruitment.worker.document', 'worker_id', string="Documents")
    job_order_ids = fields.Many2many('hr.recruitment.job.order', string="Job Orders")

class RecruitmentWorkerDocument(models.Model):
    _name = 'hr.recruitment.worker.document'
    _description = 'Worker Document'

    name = fields.Char(string="Document Name", required=True)
    file = fields.Binary(string="File", required=True)
    file_name = fields.Char(string="File Name")
    worker_id = fields.Many2one('hr.recruitment.worker', string="Worker", required=True, ondelete="cascade")


class Workers(models.Model):
    _name = "workers"
    _description = "Workers Name"
    _rec_name = "worker"

    worker = fields.Char()
    nationality = fields.Many2one(
        'res.country', string="Nationality",tracking=True)
    id_number = fields.Char(string="ID/Passport Number", tracking=True)

    skills = fields.Text(string="Skills")
    languages_ids = fields.Many2one('res.lang', string="Languages" )
    job_title = fields.Char(string="Job Title")
    experience_years = fields.Integer(string="Years of Experience")