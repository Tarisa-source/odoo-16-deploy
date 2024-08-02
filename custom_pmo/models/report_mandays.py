import ast
import logging

_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from datetime import datetime

class ReportMandays(models.Model):
    _inherit = 'project.project'

    status = fields.Selection([
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ], string="Status", store=True)

    year = fields.Char(string='year', compute="_compute_year")
    used_year = fields.Integer(string='Used Year', store=True)
    used = fields.Integer(string='Used', store=True)
    author_ids = fields.One2many('project.author', 'project_id', string="Authors")
    project_report_ids = fields.One2many('project.report', 'project_id', string="Project", ondelete='cascade')

    @api.depends('project_report_ids')
    def _compute_year(self):
        current_year = datetime.now().year
        for record in self:
            record.year = current_year

    @api.model
    def update_project_used(self):
        query = """
                WITH author_counts AS (
                    SELECT
                        pr.project_id,
                        -- Menggunakan LEAST untuk mengatur individual_count ke 1 jika lebih dari 1
                        LEAST(COUNT(1), 1) AS individual_count
                    FROM
                        project_report pr
                    GROUP BY
                        pr.project_id,
                        TO_CHAR(pr.report_date, 'YYYY-MM-DD'),
                        pr.author_name
                )
                -- Menghitung total_count per project_id
                SELECT
                    ac.project_id,
                    SUM(ac.individual_count) AS total_count
                FROM
                    author_counts ac
                GROUP BY
                    ac.project_id
                ORDER BY
                    ac.project_id;
            """
        self._cr.execute(query)
        results = self._cr.fetchall()
        for project_id, total_count in results:
            project = self.browse(project_id)
            if project:
                project.write({'used': total_count})

    def update_project_used_year(self):
        query = """
            WITH author_counts AS (
                SELECT
                    pr.project_name,
                    pr.project_id,
                    pr.author_name,
                    TO_CHAR(pr.report_date, 'YYYY-MM-DD') AS tanggal,
                    COUNT(1) AS individual_count
                FROM
                    project_report pr
                GROUP BY
                    pr.project_name,
                    pr.project_id,
                    pr.author_name,
                    TO_CHAR(pr.report_date, 'YYYY-MM-DD')
            ),
            filtered_counts AS (
                SELECT
                    ac.project_name,
                    ac.project_id,
                    ac.tanggal,
                    ac.author_name,
                    CASE 
                        WHEN ac.individual_count > 1 THEN 1
                        ELSE ac.individual_count
                    END AS individual_count
                FROM
                    author_counts ac
                WHERE
                    EXTRACT(YEAR FROM TO_DATE(ac.tanggal, 'YYYY-MM-DD')) = EXTRACT(YEAR FROM CURRENT_DATE)
            )
            SELECT
                project_id,
                SUM(individual_count) AS total_individual_count
            FROM
                filtered_counts
            GROUP BY
                project_id;
        """
        # Execute the query
        self._cr.execute(query)
        results = self._cr.fetchall()
        # Process the results
        for project_id, total_individual_count in results:
            # Browse the project record by project_id
            project = self.browse(project_id)
            if project:
                # Update the used_year field with total_count
                project.write({'used_year': total_individual_count})

    def action_view_report(self):
        action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id(
            'custom_pmo.action_report_mandays_tree')
        context = action['context'].replace('active_id', str(self.id))
        context = ast.literal_eval(context)
        context.update({
            'create': self.active,
            'active_test': self.active
        })
        action['context'] = context
        return action


class ProjectAuthor(models.Model):
    _name = 'project.author'
    _description = 'Project Author'

    author_id = fields.Integer('Author Id')
    name = fields.Char(string="Author Name")
    total_individual_count = fields.Integer(string="Total Individual Count")
    project_ids = fields.Many2one('project.project', string="Project")
    project_name = fields.Char('Project Name', related='project_ids.name')
    job_name = fields.Char('Job Position', store=True)

    @api.model
    def update_project_used_author(self):
        query = """
               WITH author_counts AS (
                    SELECT
                        pr.project_id,
                        pr.author_name,
                        pr.author_id,
                        e.job_title AS job_name,
                        TO_CHAR(pr.report_date, 'YYYY-MM-DD') AS tanggal,
                        COUNT(1) AS individual_count
                    FROM
                        project_report pr
                    LEFT JOIN
                        hr_employee e ON pr.author_id = e.id
                    GROUP BY
                        pr.project_id,
                        pr.author_name,
                        pr.author_id,
                        e.job_title,
                        TO_CHAR(pr.report_date, 'YYYY-MM-DD')
                ),
                adjusted_counts AS (
                    SELECT
                        ac.project_id,
                        ac.author_name,
                        ac.author_id,
                        CASE 
                            WHEN ac.individual_count > 1 THEN 1
                            ELSE ac.individual_count
                        END AS individual_count
                    FROM
                        author_counts ac
                ),
                author_totals AS (
                    SELECT
                        ac.project_id,
                        ac.author_name,
                        ac.author_id,
                        SUM(ac.individual_count) AS total_individual_count
                    FROM
                        adjusted_counts ac
                    GROUP BY
                        ac.project_id,
                        ac.author_name,
                        ac.author_id
                ),
                final_results AS (
                    SELECT
                        at.project_id,
                        at.author_name,
                        at.author_id,
                        COALESCE(ac.job_name, 'No Job Title') AS job_name, -- Menangani penulis tanpa job name
                        at.total_individual_count
                    FROM
                        author_totals at
                    LEFT JOIN
                        author_counts ac ON at.project_id = ac.project_id
                                          AND at.author_name = ac.author_name
                                          AND at.author_id = ac.author_id
                    GROUP BY
                        at.project_id,
                        at.author_name,
                        at.author_id,
                        at.total_individual_count,
                        ac.job_name
                )
                SELECT
                    project_id,
                    author_name,
                    author_id,
                    job_name,
                    total_individual_count
                FROM
                    final_results
                ORDER BY
                    project_id, author_id;
           """
        self._cr.execute(query)
        results = self._cr.fetchall()

        for row in results:
            project_id, author_name, author_id, job_name, total_individual_count = row
            if isinstance(total_individual_count, float):
                total_individual_count = int(total_individual_count)

            project = self.env['project.project'].browse(project_id)
            if project:
                existing_authors = project.author_ids.filtered(lambda a: a.author_id == author_id)
                if existing_authors:
                    existing_authors.write({'total_individual_count': total_individual_count})
                else:
                    self.env['project.author'].create({
                        'author_id': author_id,
                        'name': author_name,
                        'total_individual_count': total_individual_count,
                        'project_ids': project_id,
                        'job_name': job_name,
                    })

class ProjectReportAuthor(models.Model):
    _inherit = 'project.project'


    author_ids = fields.One2many('project.author', 'project_ids', 'Project Author')
    project_report_ids = fields.One2many('project.report', 'project_ids', 'Project Report')

    @api.model
    def action_view_author_report(self):
        _logger.info('Context: %s', self.env.context)
        context_project_id = self.env.context.get('default_project_id')
        _logger.info('Context Project ID: %s', context_project_id)



