# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools,exceptions, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # bulk_attendance_value = fields.Integer(string='Bulk Working Day')
    #
    #
    # @api.onchange('bulk_attendance_value')
    # def onchange_bulk_attendance(self):
    #     bulk_attendance = self.env['bulk.attendance'].search([('employee_id', '=', self.employee_id.id), ('month_list', '=', self.date_months)])




    # @api.onchange('employee_id', 'date_from', 'date_to')
    def bulk_attendance_of_employee(self):
        if self.employee_id.bulk_attendance_employee != True:
            if (not self.employee_id) or (not self.date_from) or (not self.date_to):
                return
            employee = self.employee_id
            date_from = self.date_from
            date_to = self.date_to
            contract_ids = []

            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            self.name = _('Salary Slip of %s for %s') % (
                employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
            self.company_id = employee.company_id

            if not self.env.context.get('contract') or not self.contract_id:
                contract_ids = self.get_contract(employee, date_from, date_to)
                if not contract_ids:
                    return
                self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

            if not self.contract_id.struct_id:
                return
            self.struct_id = self.contract_id.struct_id

            # computation of the salary input
            contracts = self.env['hr.contract'].browse(contract_ids)
            worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            self.worked_days_line_ids = worked_days_lines
            if contracts:
                input_line_ids = self.get_inputs(contracts, date_from, date_to)
                input_lines = self.input_line_ids.browse([])
                for r in input_line_ids:
                    input_lines += input_lines.new(r)
                self.input_line_ids = input_lines
        else:
            bulk_attendance = self.env['bulk.attendance'].search(
                [('emp_code', '=', self.employee_id.emp_code), ('month_list', '=', self.date_months),
                 ('year_id', '=', self.date_year)])
            # for entry in bulk_attendance:
            print('--------------------------------------', bulk_attendance)
            if bulk_attendance:
                for entry in bulk_attendance:
                    self.employee_present_days = entry.number_of_days
            else:
                raise ValidationError(_("Alert !, Selected Employee %s is Bulk Employee Category ,So You Must Import the Bulk Attendance.")
                                      %(self.employee_id.name))
        return

    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    for result in res:
                        if result.get('code') == 'LO':
                            result['amount'] = loan_line.amount
                            result['loan_line_id'] = loan_line.id
        return res

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()

    def bulk_attendance(self):
        self.onchange_employee()

class BulkAttendance(models.Model):
    _name = 'bulk.attendance'
    _description = 'Bulk Attendance'

    entry_date = fields.Date(string='Import Date', default=lambda self: fields.Date.today())
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
    employee_id = fields.Many2one('hr.employee', string='Employee', compute='_onchange_employee_code')
    emp_code = fields.Char(string='Employee ID')
    year_id = fields.Many2one('hr.payroll.year', string='Year')
    number_of_days = fields.Integer(string='Working Days')
    bulk_attendance_employee = fields.Boolean(string="Bulk Attendance", help="Bulk Attendance",
                                              related='employee_id.bulk_attendance_employee')

    # @api.constrains('emp_code', 'year_id', 'month_list')
    # def check_bulk_attendance(self):
    #     if self.employee_id.bulk_attendance_employee == False:
    #         print('Attendance----------------------------')
    #     else:
    #         bulk_att = self.env['bulk.attendance'].search([('emp_code', '=', self.emp_code),
    #                                                        ('id', '!=', self.id),
    #                                                        ('month_list', '!=', self.month_list)])
    #         for val in bulk_att:
    #             print('Bulk******************', val.emp_code)
    #             if bulk_att:
    #                 raise ValidationError(_("Alert !, Selected Employee of %s is Already have a Entry For the Month of  %s and this Year %s,"
    #                       "So You can't Create a Entry Against this Employee For this Month and Year.")
    #                     % (self.employee_id.name, self.month_list, self.year_id.name))

    #
    # @api.onchange('employee_id', 'year_id', 'month_list')
    # @api.depends('employee_id', 'year_id', 'month_list')
    # def _onchange_employee_bulk_attendance(self):
    #     bulk_list = self.env['bulk.attendance'].search([('employee_id', '=', self.employee_id.id), ('year_id', '=', self.year_id.id),
    #                                                     ('month_list', '=', self.month_list)])
    #     for same_entry in bulk_list:
    #         if self.employee_id and self.year_id and self.month_list:
    #             raise ValidationError(_("Alert !, Selected Employee of %s is Already have a Entry For the Month of  %s and this Year %s,"
    #                                     "So You can't Create a Entry Against this Employee For this Month and Year.")
    #                 % (self.employee_id.name, self.month_list,self.year_id.name))

    # @api.constrains('employee_id')
    # def _check_bulk_attendance_validity(self):
    #     print()
    #     for bulk in self:
    #         if bulk.employee_id.bulk_attendance_employee == False:
    #             raise exceptions.ValidationError(
    #                 _("Cannot create new Bulk attendance record for %s, the employee was Not Add Into Bulk Attendance List") %(bulk.employee_id.name))
    #         else:
    #             bulk_attendance2 = bulk.env['bulk.attendance'].search([
    #                 ('employee_id', '=', bulk.employee_id.id),
    #                 ('month_list', '=', bulk.month_list),
    #                 ('year_id', '=', bulk.year_id.id),
    #             ])
    #         # for emp in bulk_attendance2:
    #         print('*---------------New---------------------------', bulk_attendance2.employee_id.name)
    #         # if bulk_attendance2:
    #         #     raise exceptions.ValidationError(
    #         #         _("Alertssss !, Selected Employee of %s is Already have a Entry For the Month of  %s and this Year %s,"
    #         #           "So You can't Create a Entry Against this Employee For this Month and Year.")
    #         #         % (bulk.employee_id.name, bulk.month_list, bulk.year_id.name))




    @api.depends('emp_code')
    @api.onchange('emp_code')
    def _onchange_employee_code(self):
        for vals in self:
            emp_id = self.env['hr.employee'].search([('emp_code', '=', vals.emp_code)])
            for val in emp_id:
                name = val.id
            vals.employee_id = name
