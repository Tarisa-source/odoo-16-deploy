from odoo import models, fields, api
from bs4 import BeautifulSoup

class ProjectReport(models.Model):
    _name = 'project.report'
    _description = 'Project Report'

    report_date = fields.Datetime('Date')
    author_name = fields.Char('Author')
    body = fields.Text('Body')
    departement_name = fields.Char('Departement')
    project_name = fields.Char('Project')
    subtype_name = fields.Char('Subtype')
    mail_message_id = fields.Many2one('mail.message', string='Mail Message', readonly=True)

    @api.model
    def fetch_and_create_reports(self):
        query = """
            SELECT
                mail_message.id AS mail_message_id,
                res_partner.name AS author_name,
                hr_department.name AS departement_name,
                mail_message.date,
                mail_message.body,
                REPLACE(mail_message_subtype.name->>'en_US', '''', '') AS subtype_name,
                CONCAT(
                    REPLACE(project_project.name->>'en_US', '"', ''),
                    '*',
                    REPLACE(project_project_value.name->>'en_US', '"', ''),
                    '*',
                    REPLACE(project_milestone_project.name->>'en_US', '"', ''),
                    '*',
                    REPLACE(project_update_project.name->>'en_US', '"', '')
                ) AS project_name
            FROM
                mail_message
            LEFT JOIN
                res_partner ON mail_message.author_id = res_partner.id
            LEFT JOIN
                res_users ON res_partner.id = res_users.partner_id
            LEFT JOIN
                hr_employee ON res_users.id = hr_employee.user_id
            LEFT JOIN
                hr_department ON hr_employee.department_id = hr_department.id
            LEFT JOIN
                mail_message_subtype ON mail_message.subtype_id = mail_message_subtype.id
            LEFT JOIN
                project_project ON mail_message.res_id = project_project.id
            LEFT JOIN
                project_task AS new_task ON mail_message.model = 'project.task' AND mail_message.res_id = new_task.id
            LEFT JOIN
                project_project AS project_project_value ON new_task.project_id = project_project_value.id
            LEFT JOIN
                project_milestone AS new_milestone ON mail_message.model = 'project.milestone' AND mail_message.res_id = new_milestone.id
            LEFT JOIN
                project_project AS project_milestone_project ON new_milestone.project_id = project_milestone_project.id
            LEFT JOIN
                project_update AS new_update ON mail_message.model = 'project.update' AND mail_message.res_id = new_update.id
            LEFT JOIN
                project_project AS project_update_project ON new_update.project_id = project_update_project.id
            WHERE
                mail_message.model IN ('project.project', 'project.task', 'project.milestone', 'project.update')
        """
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        for result in results:
            # Check if the mail_message_id already exists in project.report
            existing_report = self.search([('mail_message_id', '=', result['mail_message_id'])])
            if not existing_report:
                # Clean the body field from HTML tags
                soup = BeautifulSoup(result['body'] or '', 'html.parser')
                cleaned_body = soup.get_text()

                self.create({
                    'report_date': result['date'],
                    'author_name': result['author_name'],
                    'body': cleaned_body,
                    'departement_name': result['departement_name'],
                    'project_name': result['project_name'],
                    'subtype_name': result['subtype_name'],
                    'mail_message_id': result['mail_message_id'],
                })
