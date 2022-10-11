from odoo import api, fields, models, _


class TaskPendingDetails(models.TransientModel):
    _name = 'task.pending.details'
    _description = "Task Pending Report Details"

    user_id = fields.Many2one('res.users', string='User', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def print_task_report(self):
        task_ids = self.env['project.task'].search([])
        print('================================================================', task_ids)
        for task in task_ids:
            data = {
                'ids': self.ids,
                'model': self._name,
                'form': {
                    # 'task_id': self.env.context.get('active_id'),
                    'task_id': task.id,
                    'user_id': self.user_id.id,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                },
            }
        print('==================================', data)
        return self.env.ref('project_task_report_app.task_pending_report_template').report_action(self, data=data)


class TaskPendingReport(models.AbstractModel):
    _name = 'report.project_task_report_app.task_pending_report_template'
    _description = "Project Task pending Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        user_id = data['form']['user_id']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        task_id = self.env['project.task'].browse(data['form']['task_id'])
        docs = []
        timesheet_ids = self.env['account.analytic.line'].search([
            ('user_id', '=', user_id),
            ('task_id', '=', task_id.id),
            ('task_id.date_assign', '>=', str(start_date)),
            ('task_id.date_assign', '<=', str(end_date))
        ])
        for task in timesheet_ids:
            docs.append({
                'date': task.date,
                'employee_id': task.employee_id.name,
                'name': task.name,
                'unit_amount': task.unit_amount,
            })
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'start_date': start_date,
            'end_date': end_date,
            'task_id': task_id,
        }
