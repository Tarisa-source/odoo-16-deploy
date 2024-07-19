# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, time
import logging
_logger = logging.getLogger(__name__)

class TaskChecklist(models.Model):
    _name = 'task.checklist'
    _description = 'Checklist for the task'

    task_id = fields.Many2one('project.task')
    check_box = fields.Boolean(default=False)
    name = fields.Char(string='Title', required=True, index=True)
    sequence = fields.Integer('Sequence', default=0)
    is_title = fields.Boolean('Is a title', default=False)
    title_id = fields.Many2one('task.checklist', string="Title", compute="_compute_title_id", store=True)
    line_ids = fields.One2many('task.checklist', "title_id", string="Line")
    status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('ready', 'Ready'),
        ('blocked', 'Blocked')
    ], string='Status', default=None)
    checklist_progress_grouped = fields.Char(string='Checklist Progress Grouped',
                                                compute='_compute_checklist_progress', store=True)


    @api.depends('task_id.checklist_ids.is_title', 'task_id.checklist_ids.sequence')
    def _compute_title_id(self):
        tasks = {}
        for checklist in self:
            if checklist.task_id.id not in tasks:
                tasks[checklist.task_id.id] = checklist.task_id.checklist_ids

        for cid, checklists in tasks.items():
            current_title = self.env['task.checklist']
            checklist_list = list(checklists)
            checklist_list.sort(key=lambda s: (s.sequence, not s.is_title))
            for chk in checklist_list:
                if chk.is_title:
                    current_title = chk
                elif chk.title_id != current_title:
                    chk.title_id = current_title.id

    def name_get(self):
        res = []
        for checklist in self:
            name = checklist.name
            if self.env.context.get('show_task'):
                name = "%s (%s)" % (name, checklist.task_id.name)
            res += [(checklist.id, name)]
        return res

    @api.onchange('check_box')
    def _onchange_checklist(self):
        _logger.info("Onchange method called!")
        self.task_id._compute_checklist_progress()

    @api.depends('task_id.checklist_ids.check_box')
    def _compute_checklist_progress(self):
        for checklist in self:
            if not checklist.task_id:
                checklist.checklist_progress_grouped = '0%'
                continue

            # Mengelompokkan checklist berdasarkan title_id
            grouped_titles = {}
            for task_checklist in checklist.task_id.checklist_ids:
                if task_checklist.is_title:
                    title_id = task_checklist.id
                    grouped_titles[title_id] = {
                        'total_checklists': 0,
                        'completed_checklists': 0,
                    }

            # Menghitung progres untuk setiap judul checklist
            for task_checklist in checklist.task_id.checklist_ids:
                if not task_checklist.is_title:
                    title_id = task_checklist.title_id.id
                    if not title_id:
                        _logger.warning(f"Title ID is empty for checklist ID {task_checklist.id}, skipping.")
                        continue
                    if title_id not in grouped_titles:
                        grouped_titles[title_id] = {'total_checklists': 0, 'completed_checklists': 0}
                    grouped_titles[title_id]['total_checklists'] += 1
                    if task_checklist.check_box:
                        grouped_titles[title_id]['completed_checklists'] += 1

            # Mengatur progres ke dalam judul checklist terkait
            for title_id, data in grouped_titles.items():
                if not title_id:
                    _logger.warning(f"Title ID is empty in grouped_titles, skipping.")
                    continue
                title = self.env['task.checklist'].browse(title_id)
                total_checklists = data['total_checklists']
                completed_checklists = data['completed_checklists']
                if total_checklists == 0:
                    title.checklist_progress_grouped = '0%'
                else:
                    progress = (completed_checklists / total_checklists) * 100
                    title.checklist_progress_grouped = f'{int(progress)}%'


class ProjectTask(models.Model):
    _inherit = 'project.task'

    checklist_ids = fields.One2many('task.checklist', 'task_id', required=True)
    checklist_progress = fields.Integer(string='Checklist Progress', compute='_compute_checklist_progress', store=True)
    task_age = fields.Char(compute='_compute_task_age', string='Work Item Age')
    filtered_user_ids = fields.Many2many(
        'res.users', compute='_compute_filtered_user_ids', string='Filtered Users', readonly=False)

    # assignees
    @api.depends('project_id.message_follower_ids')
    def _compute_filtered_user_ids(self):
        for task in self:
            filtered_users = task.project_id.message_follower_ids.mapped('partner_id.user_ids')
            task.filtered_user_ids = [(6, 0, filtered_users.ids)]

    def copy(self, default=None):
        default = default or {}
        new_task = super(ProjectTask, self).copy(default)
        for checklist in self.checklist_ids:
            checklist.copy(default={'task_id': new_task.id})
        return new_task

    def add_checklist_temp(self):
        return {
            'name': _('Add checklist'),
            'view_mode': 'form',
            'res_model': 'project.task.checklist.template',
            'type': 'ir.actions.act_window',
            'context': {'show_task': True, 'default_task_id': self.id},
            'target': 'new',
        }

    def reset_all_checklist(self):
        for task in self.filtered(lambda t: t.is_closed != True):
            task.checklist_ids = [(2, line.id) for line in task.checklist_ids]

    @api.depends('checklist_ids.check_box')
    def _compute_checklist_progress(self):
        for task in self:
            checklists = task.checklist_ids.filtered(lambda checklist: not checklist.is_title)
            total_checklists = len(checklists)
            _logger.info(f"Total checklists: {total_checklists} (excluding titles)")
            if total_checklists == 0:
                task.checklist_progress = 0
            else:
                completed_checklists = sum(1 for checklist in checklists if checklist.check_box)
                _logger.info(f"Completed checklists: {completed_checklists}")
                task.checklist_progress = (completed_checklists / total_checklists) * 100
                _logger.info(f"Checklist progress: {task.checklist_progress}")

    @api.depends('date_last_stage_update')
    def _compute_task_age(self):
        for task in self:
            if task.date_last_stage_update:
                last_stage_update = fields.Datetime.from_string(task.date_last_stage_update)
                today = datetime.today()
                age_in_days = (today - last_stage_update).days
                task.task_age = str(age_in_days)
            else:
                task.task_age = "No Update"


