from odoo import models, fields, api
from bs4 import BeautifulSoup

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    departure_date_pmo = fields.Date(string='Departure Date', related="departure_date", groups="")
    departure_reason_id_pmo = fields.Many2one('hr.departure.reason',groups="", string='Departure Reason', related="departure_reason_id")
    departure_description_pmo = fields.Html(string='Departure Description', groups="",related="departure_description")
