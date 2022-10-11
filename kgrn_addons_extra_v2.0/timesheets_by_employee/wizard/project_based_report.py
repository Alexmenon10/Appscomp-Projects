from odoo import api, fields, models, _


class ProjectBasedWizard(models.TransientModel):
    _name = 'project.based.wizard'
    _description = "Project Based Report Details"

    user_id = fields.Many2one('res.users', string='User', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    project_id = fields.Many2many('project.project', string="Project", required=True)

    def print_project_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'user_id': self.user_id.id,
                'user_name': self.user_id.name,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'project_id': self.project_id.ids,
            },
        }
        return self.env.ref('timesheets_by_employee.project_base_wizards_action').report_action(self, data=data)

class ProjectProjectReport(models.AbstractModel):
    _name = 'report.timesheets_by_employee.project_base_timesheets_qweb'
    _description = "Project Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        user_id = data['form']['user_id']
        user_name = data['form']['user_name']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        project_id = data['form']['project_id']
        docs = []

        project_ids = self.env['project.task'].search(
            [('user_ids', 'in', [user_id]), ('project_id', 'in', project_id), ('date_assign', '>=', start_date),
             ('date_assign', '<=', end_date)])

        for task in project_ids:
            vals = {
                'name': task.name,
                'user_id': task.user_ids.name,
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
            'project_id': project_id,
            'user_name': user_name,
            'user_id': user_id,
        }
