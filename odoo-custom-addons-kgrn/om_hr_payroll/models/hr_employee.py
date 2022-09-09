# -*- coding:utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta



class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    slip_ids = fields.One2many('hr.payslip', 'employee_id', string='Payslips', readonly=True)
    payslip_count = fields.Integer(compute='_compute_payslip_count', string='Payslip Count',
                                   groups="om_om_hr_payroll.group_hr_payroll_user")
    date_of_joining = fields.Date(string='Date Of Joining', required=True)
    leave_eligible_date = fields.Date(string='Leave Eligible Date')
    actual_carry_over_remarks = fields.Char(string='Approver Remarks')
    carry_over = fields.Boolean(string='Carry Over')
    carry_over_approved_by = fields.Char(string="Carry Over Approved By")
    carry_over_approved_date = fields.Datetime(string="Carry Over Approved By")
    actual_carry_over_leave = fields.Float(string='Balance Carry Over Leave')
    approved_leave = fields.Float(string='Carry Over Approved Leave')
    internal_leave_deduction = fields.Float(string='Internal Leave Deduction')
    last_day_of_current_month = date.today() + timedelta(days=30)
    Employee_one_year_completion = fields.Date(string="Employee Year Completion")
    employee_eligible_period = fields.Integer(string='Eligible Period After', store=True, default=1)


    # @api.depends('date_of_joining')
    # def _onchange_year_completion(self):
    #     import datetime
    #     if self.Employee_one_year_completion ==0:
    #         self.Employee_one_year_completion = self.date_of_joining + datetime.timedelta(days=1 * 365)

    def _compute_payslip_count(self):
        for employee in self:
            employee.payslip_count = len(employee.slip_ids)
    #
    # @api.onchange('eligible_period','leave_eligible_date')
    # def find_leave_eligible_date(self):
    #     if self.eligible_period == '1_month':
    #         self.leave_eligible_date = self.last_day_of_current_month
    #     elif self.eligible_period == '2_month':
    #         self.leave_eligible_date = self.last_day_of_current_month + timedelta(days=60)
    #     elif self.eligible_period == '3_month':
    #         self.leave_eligible_date = self.last_day_of_current_month + timedelta(days=90)
    #     elif self.eligible_period == '4_month':
    #         self.leave_eligible_date = self.last_day_of_current_month + timedelta(days=120)
    #     elif self.eligible_period == '5_month':
    #         self.leave_eligible_date = self.last_day_of_current_month + timedelta(days=150)
    #     elif self.eligible_period == '6_month':
    #         self.leave_eligible_date = self.last_day_of_current_month + timedelta(days=180)

    @api.onchange('employee_eligible_period', 'date_of_joining' 'leave_eligible_date')
    def find_leave_eligible_date(self):
        for rec in self:
            if rec.date_of_joining or rec.employee_eligible_period > 0:
                last_day_of_current_month = rec.date_of_joining
                if last_day_of_current_month and rec.employee_eligible_period:
                    # importing pandas as pd
                    import pandas as pd
                    # Creating the Series
                    sr = pd.Series(pd.date_range(last_day_of_current_month,
                                                 periods=rec.employee_eligible_period, freq='M'))
                    domain = []
                    for line in sr:
                        domain.append(line)
                    current_day = last_day_of_current_month.day
                    rec.leave_eligible_date = line + timedelta(days=current_day)

