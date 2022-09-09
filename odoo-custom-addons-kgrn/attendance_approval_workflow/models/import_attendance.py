from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError


class ImportManualAttendance(models.Model):
    _name = 'import.manual.attendance'
    _description = 'Import Manual Attendance'

    def _default_employee(self):
        emp_ids = self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    @api.model
    def default_get(self, fields):
        result = super(ImportManualAttendance, self).default_get(fields)
        line_val = []
        employee_id = self.env['hr.employee'].search([('bulk_attendance_employee', '=', True)])
        for rec in employee_id:
            line = (0, 0, {
                'emp_code': rec.emp_code,
            })
            line_val.append(line)
        result.update({
            'import_bulk_ids': line_val,
        })
        return result

    name = fields.Char(string="Name")
    reference = fields.Char(string="Reference", default=lambda self: _('New'))
    # responsible = fields.Many2one('hr.employee', string="Responsible", default='_default_employee')
    responsible = fields.Many2one('hr.employee', string='Responsible', default=_default_employee)
    date = fields.Date(string="Date", default=lambda self: fields.Date.today())
    month_list = fields.Selection([
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ], string="Month")
    year_id = fields.Many2one('hr.payroll.year', string='Year')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('created', 'Processed')], default='draft')
    import_ids = fields.One2many('import.attendance', 'import_id', string='Import Attendance', store=True)
    import_bulk_ids = fields.One2many('import.bulk.attendance', 'import_bulk_id', string='Import Bulk Attendance',
                                      store=True)

    @api.constrains('year_id', 'month_list')
    def _check_name(self):
        for record in self:
            if record.year_id and record.month_list:
                domain = [('year_id', '=', record.year_id.id), ('month_list', '=', record.month_list)]
                code = self.search(domain)
                if len(code) > 1:
                    for i in range(len(code)):
                        if code[i].id != record.id:
                            raise ValidationError(
                                _('Alert !!.'))

    def action_attendance_import(self):
        action = self.env.ref('attendance_approval_workflow.action_attendance_import_wizard').read()[0]
        action.update({'views': [[False, 'form']]})
        return action

    def bulk_attendance_create(self):
        print('*******************************************')
        for val in self.import_bulk_ids:
            vals = self.env['bulk.attendance'].create({
                'emp_code': val.emp_code,
                'number_of_days': val.total_days,
                'month_list': self.month_list,
                'year_id': self.year_id.id,
            })
            self.write({
                'state': 'created',
            })

    # def attendance_import_validation(self):
    #     line_value = []
    #     attendance = self.env['hr.attendance']
    #     for line in self.import_ids:
    #         line_val = {
    #             'emp_code' : line.emp_code,
    #             'check_in' : line.check_in,
    #             'check_out' : line.check_out
    #         }
    #         line_value.append(line_val)
    #         attendance.create(line_value)
    #         print('*------------------------------------------------*', line_value)

    def attendance_import_validation(self):
        # if self.env.context.get('active_model') == 'import.manual.attendance':
        active_id = self.env.context.get('active_id', False)
        indent_id = self.env['import.manual.attendance'].search([('id', '=', active_id)])
        for line in self.import_ids:
            contract = self.sudo().env['hr.attendance'].sudo().search([
                ('emp_code', '=', line.emp_code),
                ('check_in', '<=', line.check_in),
                ('id', '!=', line.id)])
        line_value = []
        if not contract:
            for line in self.import_ids:
                line_val = {
                    'emp_code': line.emp_code,
                    'check_in': line.check_in,
                    'check_out': line.check_out
                }
                line_value.append(line_val)
                self.sudo().env['hr.attendance'].create(line_value)
        return contract

    def bulk_attendance_wizard(self):
        action = self.env.ref('attendance_approval_workflow.action_bulk_attendance_wizard').read()[0]
        action.update({'views': [[False, 'form']]})
        return action

    @api.model
    def create(self, values):
        values['reference'] = self.sudo().env['ir.sequence'].get('import.manual.attendance') or '/'
        res = super(ImportManualAttendance, self).create(values)
        return res

class ImportAttendance(models.Model):
    _name = 'import.attendance'
    _description = 'Import Attendance'

    import_id = fields.Many2one('import.manual.attendance', string="Import Attendance")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  ondelete='cascade', index=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id",
                                    readonly=True)
    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)
    emp_code = fields.Char(string='Employee ID')
    custom_state = fields.Selection([
        ('draft', 'New'),
        ('post', 'Posted'),
        ('reject', 'Rejected')],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        default='draft'
    )

    @api.depends('emp_code')
    @api.onchange('emp_code')
    def _onchange_employee_code(self):
        for vals in self:
            emp_id = self.env['hr.employee'].search([('emp_code', '=', vals.emp_code)])
            for val in emp_id:
                employee_name = val.id
            vals.employee_id = employee_name

    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for vals in self:
            if vals.employee_id:
                employee_id = self.env['hr.employee'].search([('name', '=', vals.employee_id.name)])
                for val in employee_id:
                    code = val.emp_code
                vals.emp_code = code

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False


class ImportBulkAttendance(models.Model):
    _name = 'import.bulk.attendance'
    _description = 'Import Bulk Attendance'

    import_bulk_id = fields.Many2one('import.manual.attendance', string="Import Bulk Attendance")
    emp_code = fields.Char(string='Employee ID')
    total_days = fields.Integer(string='Working Day')
