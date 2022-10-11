from odoo import api, fields, models, _


class ProjectTaskPendingDetails(models.TransientModel):
    _name = 'project.task.pending.details'
    _description = "Task Pending Report Details"

    user_id = fields.Many2one('res.users', string='User', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def print_report_pending(self):
        project_id = self.env.context.get('active_id')
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'project_id': project_id,
                'user_id': self.user_id.id,
                'user_name': self.user_id.name,
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
        }
        return self.env.ref('timesheets_by_employee.task_pending_action_report').report_action(self, data=data)

class TaskPendingReport(models.AbstractModel):
    _name = 'report.timesheets_by_employee.task_pending_template_qweb'
    _description = "Project Task pending Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        user_id = data['form']['user_id']
        user_name = data['form']['user_name']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        project_id = data['form']['project_id']
        docs = []
        task_ids = self.env['project.task'].search(
            [('user_ids', 'in', [user_id]), ('date_assign', '>=', start_date),
             ('date_assign', '<=', end_date)])
        for task in task_ids:
            if task.planned_hours < task.effective_hours:
                vals = {
                    'name': task.name,
                    'user_id': task.user_ids,
                    'stage': task.stage_id.name,
                    'planned_hours': task.planned_hours,
                    'total_hours_spent': task.total_hours_spent,
                    'remaining_hours': task.remaining_hours,
                    'date_assign': task.date_assign.date(),
                    'date_deadline': task.date_deadline,
                    'project': task.project_id.name,
                    'stages': task.stage_id.name,
                }
                docs.append(vals)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'start_date': start_date,
            'end_date': end_date,
            'project_id': self.env['project.project'].browse(project_id),
            'user_name': user_name,
            'user_id': user_id,
        }
