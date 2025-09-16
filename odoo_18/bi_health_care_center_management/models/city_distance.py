from odoo import models, fields, api


class CityDistance(models.Model):
    _name = 'city.distance'
    _description = 'City Distance Information'

    name = fields.Char(compute="_compute_name", store=True)

    city_options = [
        ('muaither', 'Muaither'),
        ('doha', 'Doha'),
        ('al_wakrah', 'Al Wakrah'),
        ('al_khor', 'Al Khor'),
        ('mesaieed', 'Mesaieed'),
        ('al_rayyan', 'Al Rayyan'),
        ('lusail', 'Lusail'),
        ('al_shamal', 'Al Shamal'),
        ('dukhan', 'Dukhan'),
        ('umm_salal', 'Umm Salal'),
        ('al_ghuwariyah', 'Al Ghuwariyah'),
        ('al_jumayliyah', 'Al Jumayliyah'),
        ('al_dhakira', 'Al Dhakira'),
        ('umm_bab', 'Umm Bab'),
        ('rawdat_rashid', 'Rawdat Rashid'),
        ('umm_al_amad', 'Umm Al Amad'),
        ('al_wukair', 'Al Wukair'),
        ('fuwayrit', 'Fuwayrit'),
        ('abu_nakhla', 'Abu Nakhla'),
        ('umm_said', 'Umm Said (Mesaieed Industrial)'),
        ('rawdat_abalirq', 'Rawdat Abalirq'),
    ]

    from_city = fields.Selection(city_options, string='From City', default='muaither', required=True, readonly=True)
    to_city = fields.Selection(city_options[1:], string='To City', required=True)

    distance_km = fields.Float(string='Distance (km)', required=True)
    travel_time = fields.Float(string='Estimated Travel Time', required=True)

    @api.onchange('travel_time')
    def _on_change_joker(self):
        print(self.travel_time)


    @api.depends('from_city', 'to_city')
    def _compute_name(self):
        for record in self:
            record.name = f"{dict(self.city_options).get(record.from_city, '')} -> {dict(self.city_options).get(record.to_city, '')}"