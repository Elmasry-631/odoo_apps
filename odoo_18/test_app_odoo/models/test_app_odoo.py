from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TestAppOdoo(models.Model):
    _name = 'test.app.odoo'

    name = fields.Char()
    description = fields.Text()
    active = fields.Boolean(default=True)
    value = fields.Integer()

    @api.constrains('value')
    def _check_value(self):
        for rec in self:
            if rec.value <= 0:
                raise ValidationError("Value must be greater than zero.")

    @api.constrains('value')
    def _check_value(self):
        for rec in self:
            if rec.value != int:
                raise ValidationError("Value must be an integer.")
