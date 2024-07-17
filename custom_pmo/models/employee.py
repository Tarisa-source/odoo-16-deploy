from odoo import models, fields, api
from datetime import datetime, date

class CustomEmployee(models.Model):
    _inherit = 'hr.employee'

    is_in_specific_division = fields.Boolean(string='Is in Specific Division', compute='_compute_is_in_specific_division')
    lama_bekerja = fields.Char(string='Lama Bekerja', compute='_compute_lama_bekerja')

    def _compute_is_in_specific_division(self):
        for employee in self:
            employee.is_in_specific_division = employee.department_id.name == 'PMO'

    def _compute_lama_bekerja(self):
        for employee in self:
            if employee.x_tanggal_masuk:
                start_date = fields.Date.from_string(employee.x_tanggal_masuk)
                today = date.today()
                delta = today - start_date

                years = delta.days // 365
                remaining_days = delta.days % 365
                months = remaining_days // 30
                days = remaining_days % 30

                employee.lama_bekerja = f"{years} tahun, {months} bulan, {days} hari"
            else:
                employee.lama_bekerja = "N/A"
