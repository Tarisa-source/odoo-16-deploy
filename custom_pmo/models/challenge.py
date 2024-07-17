from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Challenge(models.Model):
    _name = 'challenge'
    _description = 'Challenge PMO'
    _rec_name = 'employee_pmo'

    employee_pmo = fields.Many2one('res.users', string='Name', auto_join=True, tracking=True, required=True)
    promote_level = fields.Selection([
        ('PM','Project Manager'),
        ('leader', 'Leader'),
        ('system_analyst', 'System Analyst'),
        ('developet_analyst', 'Developer Analyst'),
        ('developer', 'Developer'),
    ], default=False, index=True, string="Promote Level", tracking=True, required=True)
    start_challenge = fields.Date(string='Start Challenge', index=True, required=True)
    end_date = fields.Date(string='End Challenge', index=True, required=True)
    status_challenge = fields.Selection([
        ('plan', 'Plan'),
        ('in progress', 'In Progress'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status Challenge', index=True, tracking=True, required=True)
    notes = fields.Char(string="Notes", help='Free text penjelasan kenapa berhasil dan kenapa gagal')
    asesor = fields.Many2many('hr.employee', relation='challenge_employee_rel', column1='challenge_id', column2='employee_id', string='Assessor', context={'active_test': False}, tracking=True, required=True)

    @api.constrains('start_challenge', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_challenge and record.end_date < record.start_challenge:
                raise ValidationError('The start date must be earlier than the end date.')


