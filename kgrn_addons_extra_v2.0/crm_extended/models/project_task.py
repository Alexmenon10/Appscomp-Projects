# -*- coding: utf-8 -*-
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlwt
import base64
from xlwt import easyxf
import io
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
import datetime
from odoo.exceptions import UserError
from datetime import datetime
import pdb
import io


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
    task_attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment")
    extend_hours = fields.Float(string='Extended Hours')
    approved_extend_hours = fields.Float(string='Approved Extended Hours')
    extend_hours_check = fields.Boolean(string='Check')
    extend_hours_approve_check = fields.Boolean(string='Check')
    time_extended_request_to_approve = fields.Boolean(string='Waiting For Time Extended')
    time_extended_request_approved = fields.Boolean(string='Time Extended Approve')
    time_extended_request_rejected = fields.Boolean(string='Time Extended Rejected')
    # user_ids = fields.Many2one('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id',
    #                            string='Assignees', default=lambda self: not self.env.user.share and self.env.user,
    #                            context={'active_test': False}, tracking=True)

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

    @api.onchange('start_date', 'end_date')
    def _onchange_date_validation(self):
        if self.start_date and self.end_date:
            task_s_date = self.start_date.date()
            task_e_date = self.end_date.date()
            timedelta = self.end_date - self.start_date
            tot_sec = timedelta.total_seconds()
            h = tot_sec // 3600
            m = (tot_sec % 3600) // 60
            duration_hour = ("%d.%d" % (h, m))
            self.planned_hours = float(duration_hour)
            # if self.start_date > self.end_date:
            #     raise ValidationError(_('Alert, You Cannot Select this Date.'))
            # if not self.project_id.date_start <= task_s_date <= self.project_id.date:
            #     raise ValidationError(_('Alert, You Cannot Select this Date.'))
            # if not self.project_id.date_start <= task_e_date <= self.project_id.date:
            #     raise ValidationError(_('Alert, You Cannot Select this Date.'))

    @api.onchange('effective_hours')
    def planned_hours_extence(self):
        if self.planned_hours < self.effective_hours:
            value = (20 / self.planned_hours) * 100
            self.write({
                'extend_hours': value,
                'extend_hours_check': True,
            })
            extend_hour_2 = self.planned_hours + value
            if extend_hour_2 < self.effective_hours:
                print('================================', value, extend_hour_2)
                self.write({
                    'extend_hours_approve_check': True,
                })

    def request_to_time_extended(self):
        print('=-')
        self.write({
            'time_extended_request_to_approve': True,
        })

    def approved_time_extended(self):
        print('----')
        if self.approved_extend_hours == 0.00:
            raise ValidationError(_('Alert, Extened Hours.'))
        self.write({
            'time_extended_request_approved': True,
            'extend_hours_approve_check': False,
        })

    def rejected_time_extended(self):
        print('----')
        self.write({
            'time_extended_request_rejected': True,
        })

    # def task_complete_request_to_approve(self):
    #     self.ensure_one()
    #     lang = self.env.context.get('lang')
    #     ir_model_data = self.env['ir.model.data']
    #     # template_id = ir_model_data._xmlid_lookup('crm_extended.rrrrrrrrr')
    #     # template = self.env['mail.template'].browse(template_id)
    #     template = self.env.ref('crm_extended.rrrwwrrrrrr',
    #                             False)
    #     template.sudo().send_mail(self.id, force_send=True)
    #     current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
    #     ctx = {
    #         'default_model': 'project.task',
    #         'default_res_id': self.ids[0],
    #         # 'default_use_template': bool(template_id),
    #         # 'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'mark_so_as_sent': True,
    #         'custom_layout': "mail.mail_notification_paynow",
    #         # 'proforma': self.env.context.get('proforma', False),
    #         'force_email': True,
    #         'model_description': self.with_context(lang=lang),
    #         'name': self.name,
    #         'url': current_url,
    #         'email_to': self.user_ids.employee_id.work_email,
    #         'email_from': self.project_id.user_id.employee_id.work_email,
    #         'project_name': self.project_id.name,
    #         'employee_name': self.user_ids.name,
    #         'manager_name': self.project_id.user_id.name,
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def task_complete_request_to_approve(self):
        ctx = self.env.context.copy()
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'name': self.name,
            'url': current_url,
            # 'email_to': self.user_ids.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            # 'employee_name': self.user_ids.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.rrrwwrrwwrrrrrrrrrrrreqqrssrr',
                                False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        self.request_to_approve = True

    def task_complete_approved(self):
        ctx = self.env.context.copy()
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'name': self.name,
            'url': current_url,
            'email_to': self.user_ids.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            'employee_name': self.user_ids.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.eeeeeeeeweeeeeewwerreeeeeeeeteeeeeeeee',
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
            'email_to': self.user_ids.employee_id.work_email,
            'email_from': self.project_id.user_id.employee_id.work_email,
            'project_name': self.project_id.name,
            'employee_name': self.user_ids.name,
            'manager_name': self.project_id.user_id.name,
        })
        template = self.env.ref('crm_extended.pqqq',
                                False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        self.update({'request_rejected': True})

    def action_get_excess_time_spend_task(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Excess Time Spend Task Report')

        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        worksheet1.col(0).width = 1800
        worksheet1.col(1).width = 4300
        worksheet1.col(2).width = 6000
        worksheet1.col(3).width = 4000
        worksheet1.col(4).width = 5000
        worksheet1.col(5).width = 4800
        worksheet1.col(6).width = 4800
        worksheet1.col(7).width = 4300
        worksheet1.col(8).width = 4800
        worksheet1.col(9).width = 3500
        worksheet1.col(10).width = 3500
        worksheet1.col(11).width = 3500
        worksheet1.col(12).width = 3500
        worksheet1.col(13).width = 5000
        worksheet1.col(14).width = 5000
        worksheet1.col(15).width = 5000

        rows = 0
        cols = 0
        row_pq = 3

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        import datetime
        de_s_date = (date.today().replace(day=1))
        de_en_date = (datetime.datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 6, 'EXCESS TIME SPEND TASK REPORT', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'START DATE', design_14)
        worksheet1.write(rows, 4, de_s_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'END DATE', design_14)
        worksheet1.write(rows, 4, de_en_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PROJECT NAME'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TASK NAME'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('ASSIGNEE'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PLANNED HOURS'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TOTAL HOURS'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('DIFFERENT'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('DURATION'), design_13)

        sl_no = 1
        row_pq = row_pq + 1
        mr_num = []
        res = []
        # for record in self:
        start_date = de_s_date
        end_date = de_en_date
        import datetime
        d11 = str(start_date)
        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d')
        starts_process = dt21.strftime("%d/%m/%Y %H:%M:%S")
        d22 = str(end_date)
        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
        ends_process = dt22.strftime("%d/%m/%Y %H:%M:%S")
        domain = [
            ('end_date', '>=', starts_process),
            ('end_date', '<=', ends_process),
        ]
        # if de_s_date and de_en_date:
        task_id = self.env['project.task'].sudo().search(domain)
        for task in task_id:
            if task.planned_hours < task.effective_hours:
                start_date = task.start_date
                end_date = task.end_date
                duration = end_date - start_date
                worksheet1.write(row_pq, 0, sl_no, design_7)
                if task.project_id.name:
                    worksheet1.write(row_pq, 1, task.project_id.name, design_8)
                else:
                    worksheet1.write(row_pq, 1, '-', design_7)
                if task.name:
                    worksheet1.write(row_pq, 2, task.name, design_8)
                else:
                    worksheet1.write(row_pq, 2, '-', design_7)
                if task.user_ids.name:
                    worksheet1.write(row_pq, 3, task.user_ids.name, design_8)
                else:
                    worksheet1.write(row_pq, 3, '-', design_7)
                if task.planned_hours:
                    worksheet1.write(row_pq, 4, task.planned_hours, design_8)
                else:
                    worksheet1.write(row_pq, 4, '-', design_7)
                if task.effective_hours:
                    worksheet1.write(row_pq, 5, task.effective_hours, design_8)
                else:
                    worksheet1.write(row_pq, 5, '-', design_7)
                if task.remaining_hours:
                    worksheet1.write(row_pq, 6, abs(task.remaining_hours), design_8)
                else:
                    worksheet1.write(row_pq, 6, '-', design_7)
                if duration:
                    worksheet1.write(row_pq, 7, str(duration), design_8)
                else:
                    worksheet1.write(row_pq, 7, '-', design_7)

                sl_no += 1
                row_pq += 1
        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.b64encode(fp.getvalue())
        fp.close()
        return excel_file

    def cron_excess_time_spend_task_report(self):
        from datetime import datetime, date
        today = datetime.today().date()
        import datetime
        today_print = today.strftime("%d/%m/%Y")
        data = self.action_get_excess_time_spend_task()
        ir_values = {
            'name': "Excess Time Spend Task Report_%s.xls" % today_print,
            'type': 'binary',
            'datas': data,
            'store_fname': data,
            # 'mimetype': 'text/csv',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        body = """
            Dear Team,
            <br/>
            <br/>
            Enquiries are not updated since 2 days by sales persons as listed in the attached report. Please find the attachment.
                <br/>
                <br/>
            Regards,<br/>
            Administrator
            <p align="center">----------------------------------This is a system generated email----------------------------------------------</p>"""
        import datetime
        today_print = today.strftime("%d/%m/%Y")
        mail_value = {
            'subject': 'Leads Not Updated since Last 2 Days (%s)' % (today_print),
            'body_html': body,
            # 'email_cc': "m.ashif@hidayath.com",
            'email_to': "alexmenonappscomp@gmail.com",
            'email_from': "praveen.appscomp@gmail.com",
            'attachment_ids': [(6, 0, [data_id.id])],
        }
        self.env['mail.mail'].create(mail_value).send()


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
