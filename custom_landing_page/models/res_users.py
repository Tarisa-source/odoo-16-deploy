from odoo import models, api
from datetime import datetime

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def action_open_attendance_or_project(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if employee:
            today = datetime.now().date()
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                ('check_in', '<=', datetime.combine(today, datetime.max.time()))
            ], limit=1)
            if attendance:
                return self.env.ref('project.open_view_project_all_group_stage').read()[0]  # Menu Project
            else:
                return self.env.ref('hr_attendance.hr_attendance_action_my_attendances').read()[0]  # Menu Attendance
        return self.env.ref('hr_attendance.hr_attendance_action_my_attendances').read()[0]  # Default ke Menu Attendance
