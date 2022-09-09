# -*- coding: utf-8 -*-
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, exceptions, api, _
import tempfile
import binascii


class Task(models.Model):
    _inherit = "project.task"

    request_to_approve = fields.Boolean(string='Waiting For Approve')
    request_approved = fields.Boolean(string='Approved')
    request_rejected = fields.Boolean(string='Rejected')
    stage_name = fields.Char(string='Approved')
    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High')],
        string='Priority')
    # user_ids = fields.Many2many(
    #     'res.users',
    #     string='Assignees',
    #     tracking=True
    # )
    # state = fields.Selection([('draft', 'New'),
    #                           ('confirm', 'Confirmed'),
    #                           ('approved', 'Approved'),
    #                           ('reject', 'Rejected'),
    #                           ('cancel', 'Cancelled')],
    #                          string='State', default='draft')


    @api.onchange('stage_id')
    @api.depends('stage_id')
    def _get_stage_name(self):
        if self.stage_id.name == 'Done':
            raise ValidationError(_('Alert.....'))
        self.stage_name = self.stage_id.name

    def task_complete_request_to_approve(self):
        ctx = self.env.context.copy()
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'name': self.name,
            'url': current_url,
            'email_to': self.user_id.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            'employee_name': self.user_id.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.rrrrr',
                                False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        self.request_to_approve = True
        # self.write({
        #     'request_to_approve': True,
        #     'stage_id': '',
        # })

    def task_complete_approved(self):
        ctx = self.env.context.copy()
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'name': self.name,
            'url': current_url,
            'email_to': self.user_id.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            'employee_name': self.user_id.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.eeeeeeeeweeeeeewweeeeeeeteeeeeee',
                                False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        self.update({'request_approved': True})

    def task_complete_reject(self):
        ctx = self.env.context.copy()
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'name': self.name,
            'url': current_url,
            'email_to': self.user_id.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            'employee_name': self.user_id.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.pq',
                                False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        self.update({'request_rejected': True})



# class ProjectTaskType(models.Model):
#     _inherit = 'project.task.type'
#
#     @api.model
#     def default_get(self, fields):
#         result = super(ProjectTaskType, self).default_get(fields)
#         project_id = self.env['project.project'].search([])
#         if project_id:
#             result.update({
#                 'project_ids': project_id.ids,
#             })
#         return result


class ProjectProject(models.Model):
    _inherit = "project.project"


    def action_view_tasks(self):
        res = super(ProjectProject, self).action_view_tasks()
        project_stage = self.env['project.task.type'].search([
            ('name', '=', 'In Progress'), ('name', '=', 'Draft')])
        for stage in project_stage:
            print('/////////////////////////////////////', stage.name)
        return res


    @api.model
    def create(self, vals):
        res = super(ProjectProject, self).create(vals)
        res.action_view_tasks()
        return res


class MyimportWizard(models.TransientModel):
    _name = 'my.import.wizard'
    _description = 'My import Wizard'
    # your file will be stored here:
    data_file = fields.Binary(string='XLS File')
    file_name = fields.Char('Filename')

    def import_csv(self, xlrd=None):
        active_id = self.env['bulk.attendance']
        # bom_line = self.env['mrp.bom.line']
        for bulk_attendance in self:
            if not bulk_attendance.file_name:
                print("no file found")
                return False
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.data_file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            print('****************************************-------------------')
            reader = []
            keys = sheet.row_values(0)
            values = [sheet.row_values(i) for i in range(1, sheet.nrows)]
            for value in values:
                reader.append(dict(zip(keys, value)))
            print('*-----------------------------------------------***', reader)
            for line in reader:
                active_ids = self.env['bulk.attendance']
                vals = {
                    'emp_code': line.get('product_qty'),
                    'product_id': int(line.get('product_id')),
                    'product_qty': line.get('product_qty')
                }
                active_ids.create(vals)
        return True
