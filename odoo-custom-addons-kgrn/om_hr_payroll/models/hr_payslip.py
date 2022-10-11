# -*- coding:utf-8 -*-

import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import timedelta


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _description = 'Pay Slip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True, states={'draft': [('readonly', False)]},
                                help='Defines the rules that have to be applied to this payslip, accordingly '
                                     'to the contract chosen. If you let empty the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules applied will be all the rules set on the '
                                     'structure of all contracts of the employee valid for the chosen period')
    name = fields.Char(string='Payslip Name', readonly=True,
                       states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False,
                         states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          states={'draft': [('readonly', False)]})
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5 exist ('confirm' seems to have existed)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
                               states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    worked_days_line_ids = fields.One2many('hr.payslip.worked_days', 'payslip_id',
                                           string='Payslip Worked Days', copy=True, readonly=True,
                                           states={'draft': [('readonly', False)]})
    input_line_ids = fields.One2many('hr.payslip.input', 'payslip_id', string='Payslip Inputs',
                                     readonly=True, copy=True, states={'draft': [('readonly', False)]})
    paid = fields.Boolean(string='Made Payment Order ? ', readonly=True, copy=False,
                          states={'draft': [('readonly', False)]})
    note = fields.Text(string='Internal Note', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
                                  states={'draft': [('readonly', False)]})
    details_by_salary_rule_category = fields.One2many('hr.payslip.line',
                                                      compute='_compute_details_by_salary_rule_category',
                                                      string='Details by Salary Rule Category')
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Indicates this payslip has a refund of another")
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True,
                                     copy=False, states={'draft': [('readonly', False)]})
    payslip_count = fields.Integer(compute='_compute_payslip_count', string="Payslip Computation Details")
    unpaid_deduction = fields.Float(string="Unpaid Amount Deduction")
    bday_allowance = fields.Float(string="Birthday Allowance", default=500)
    flt_allowance = fields.Float(string="Flight Allowance", default=700)
    loan_deduction = fields.Boolean(string='Loan Deduction', readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    help="Indicates this payslip has a loan payment deduction")
    gross_deduction_amount = fields.Float(string="Gross Deduction Amount")
    basic_deduction_amount = fields.Float(string="Basic Deduction Amount")
    house_deduction_amount = fields.Float(string="HRA Deduction Amount")
    deduction_amount = fields.Float(string="Deduction Amount")
    remarks = fields.Text(string="Loan Payment Remarks",
                          default="Gross Amount Deduction(50%),Basic Amount Deduction(40%)")
    employee_one_day_salary = fields.Float(string="Employee One Day Amount")
    employee_loptotal_days = fields.Integer(string="Employee LOP Days")
    employee_present_days = fields.Integer(string="Employee Present Days")
    employee_final_present_days = fields.Integer(string="Employee Total Payable Days")
    employee_balance_days = fields.Float(string="Employee Balance Days")
    date_months = fields.Char(string="Month")
    date_year = fields.Char(string="Year")
    leave_paid_timeoff = fields.Float(string="Paid Leave ")
    final_payslip_calcualte_amount = fields.Float(string="Final Pay")
    number_working_of_days = fields.Float(string="Number of working Days")
    total_number_of_days = fields.Float(string="Total Number Of Days ")
    total_balance_days = fields.Float(string="Total Balance Days ")
    public_lop_count_days = fields.Integer(string="Public leave Count")
    non_present_days = fields.Float(string='Non Present Days')
    third_friday_date = fields.Date(string='Third Friday Date')
    firday_boolean = fields.Boolean(string='Friday Boolean')
    number_of_leave = fields.Float(string="Public Leave's and Sunday's ")
    total_days_of_month = fields.Float(string="Total Days in Month ")
    employee_final_lop_total_days = fields.Integer(string="Employee Final LOP Days")

    @api.onchange('employee_id', 'date_from', 'date_to')
    def compute_days(self):
        import calendar
        import datetime
        date = datetime.datetime.now()
        month_current = calendar.monthrange(date.year, date.month)[1]
        if self.date_from.month == self.date_to.month:
            date_fr = self.date_from.month and self.date_to.month
            daten = datetime.datetime(1, int(date_fr), 1).strftime("%B")
            self.date_months = daten
        if self.date_from.year == self.date_to.year:
            date_yr = self.date_from.year and self.date_to.year
            # daten = datetime.datetime(1, int(date_fr), 1).strftime("%B")
            self.date_year = date_yr

    @api.onchange('employee_id', 'date_from', 'date_to')
    def employee_number_working_of_days_button(self):
        num_of_days = self.env['hr.payroll.year'].search([('name', '=', self.date_year)])
        for record in self:
            if num_of_days.day_and_month:
                for line in num_of_days.day_and_month:
                    # if int(line.select_month) != record.date_from.month:
                    if line.select_month != record.date_from.month:
                        record.write({
                            'number_working_of_days': 0,
                            'number_of_leave': 0,
                            'total_days_of_month': 0,
                        })

    def get_payroll_year_working_days(self):
        num_of_days = self.env['hr.payroll.year'].search([('name', '=', self.date_year)])
        if num_of_days:
            num_of_days.get_number_of_working_days()

    def employee_year_month_button(self):
        month = 0
        num_of_days = self.env['hr.payroll.year'].search([('name', '=', self.date_year)])
        for record in self:
            if num_of_days.day_and_month:
                for line in num_of_days.day_and_month:
                    if int(line.select_month) == record.date_from.month and line.boolen_leave:
                        month = record.date_from.month
                        record.get_payroll_year_working_days()
                    # if int(line.select_month) == record.date_from.month and not line.boolen_leave:
                    if line.select_month == record.date_from.month and not line.boolen_leave:
                        raise ValidationError(
                            _("Alert!,The selected Payslip Period - %s-%s,The Number of working days setup has done, "
                              "\n but, does,'t Approved Number Of Working Days setup."
                              "SO, Please, Approve the Config and generate it.") % (
                                record.date_months, record.date_year))
                if not month:
                    # print('#####################################', type(line.select_month),
                    #       type(record.date_from.month))
                    raise ValidationError(
                        _("Alert!,The selected Payslip Period, "
                          "Doesn't created  Number of Working Days setup for - %s-%s.\n"
                          "SO, Please create in the Config and generate it.") % (
                            record.date_months, record.date_year))
                # else:
                #     raise ValidationError(
                #         _("Alert!,The selected Payslip Period, "
                #           "Doesn't created  Number of Working Days setup for - %s-%s.\n"
                #           "SO, Please create in the Config and generate it.") % (
                #             record.date_months, record.date_year))
            else:
                raise ValidationError(
                    _("Alert!,The selected Payslip Period "
                      "Doesn't created Number of Working Days setup for any of the month of this year %s.\n"
                      "SO, Config and generate it.") % (
                        record.date_year))

    @api.onchange('employee_id')
    def payslip_validate(self):
        date_fro = self.date_from
        from datetime import datetime
        currentMonth = datetime.now().month
        import datetime
        datem = datetime.datetime.strptime(str(date_fro), "%Y-%m-%d")
        pay_date = self.env['hr.payslip'].search(
            [('employee_id', '=', self.employee_id.id)])
        # for pay in pay_date:
        #     if datem.month == currentMonth:
        #         raise ValidationError(_('The payslip can only be generated once'))

    def get_employee_details(self):
        employee_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        employee_leave_aa = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '=', 'Unpaid'),
             ('state', '=', 'validate')])
        friday_config = self.env['hr.payroll.year'].search([('name', '=', self.date_year)])
        num_days = 0
        up = 0
        friday_count = 0
        friday_lop_count = 0
        paid_leave_num_days = 0
        profitpercentday = 0
        total_wage = 0
        get_third_saturday = 0
        unpaid_amount_based_lop = 0
        from datetime import datetime
        currentMonth = datetime.now().month
        employee_leave_paid_time = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '!=', 'Unpaid'),
             ('state', '=', 'validate')])
        if self.employee_id:
            import calendar
            import datetime
            total_wage_contract = 0.00
            try:
                total_wage_contract = self.contract_id.wage / self.total_days_of_month
                self.employee_one_day_salary = total_wage_contract
            except ZeroDivisionError:
                total_wage_contract = 0
                self.employee_one_day_salary = total_wage_contract
            total_unpaid_amount = (self.employee_balance_days + self.employee_loptotal_days) * total_wage_contract
            self.employee_final_lop_total_days = self.employee_balance_days + self.employee_loptotal_days
            try:
                profitpercentday = (employee_contract.wage / self.total_days_of_month)
            except ZeroDivisionError:
                self.employee_one_day_salary = profitpercentday
            self.write({'employee_one_day_salary': total_wage_contract,
                        'unpaid_deduction': total_unpaid_amount})
            # AAAAAAAAAA = self.employee_final_present_days - friday_lop_count
            # self.employee_final_present_days = AAAAAAAAAA

        for aa in employee_leave_aa:
            # employee_leave = self.env['hr.leave'].search_count(
            #     [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '=', 'Unpaid'),
            #      ('state', '=', 'validate')])
            from datetime import date, timedelta
            import calendar
            import datetime
            date = datetime.datetime.now()
            diff = calendar.monthrange(date.year, date.month)[1]
            num_days += aa.number_of_days
        for bb in employee_leave_paid_time:
            employee_paid_leave = self.env['hr.leave'].search_count(
                [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '!=', 'Unpaid'),
                 ('state', '=', 'validate')])
            if self.date_from.month == bb.request_date_from.month:
                paid_leave_num_days += bb.number_of_days
                self.leave_paid_timeoff = paid_leave_num_days
                # self.final_payslip_calcualte_amount = paid_leave_num_days

        for unpaid in self.line_ids:
            if unpaid.name == 'Unpaid':
                print(unpaid.name == 'Unpaid')
                # print('unpaid amount',unpaid.amount)
                unpaid.write({
                    'amount': self.unpaid_deduction})
                employee_contract.write({
                    'unpaid_leave_amount_deduction': self.unpaid_deduction})
        for emp_aa_leave in employee_leave_aa:
            for contract_emp in employee_contract:
                if self.employee_id:
                    import calendar
                    import datetime
                    date = datetime.datetime.now()
                    diff = calendar.monthrange(date.year, date.month)[1]
                if self.date_from.month == emp_aa_leave.request_date_from.month:
                    num_dayss = emp_aa_leave.number_of_days
                    self.employee_loptotal_days = num_dayss
                    total_wage = employee_contract.wage / diff
                    # self.employee_one_day_salary = total_wage
                    # total_unpaid_amount = (self.employee_balance_days + self.employee_loptotal_days) * total_wage
                    # final_wage = employee_contract.wage - (num_dayss * total_wage)
                    # try:
                    #     profitpercentday = (employee_contract.wage / self.total_days_of_month)
                    # except ZeroDivisionError:
                    #     self.employee_one_day_salary = profitpercentday
                    # # self.write({'employee_one_day_salary': total_wage,
                    #             'unpaid_deduction': total_unpaid_amount})

    def get_public_leave_yesterday(self):
        import datetime
        from datetime import datetime
        value_count = 0.00
        leave_num_days = 0.00
        ph_lop = 0.00
        ph_lop_1 = 0.00
        ph_lop_2 = 0.00
        ph_lop_11 = 0.00
        count = 0.00
        count1 = 0.00
        count2 = 0.00
        ph_lop_3 = 0.00
        count3 = 0.00
        count4 = 0.00
        non_present = 0.00
        # ph_lop5 = 0.00
        currentMonth = datetime.now().month
        employee_attendance = self.env['hr.attendance'].search(
            [('employee_id', '=', self.employee_id.id), ('custom_state', '=', 'approve')])
        employee_leave_aa = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])
        public_leave_config = self.env['hr.holidays.public'].search([('year_id', '=', self.date_year)])
        for attend in employee_attendance:
            if currentMonth == attend.check_in.date().month:
                for ad_pub in public_leave_config.line_ids:
                    if currentMonth == ad_pub.date.month:
                        count += 1
                        public_holiday_attendance_check = ad_pub.date - timedelta(days=1)
                        if attend.check_in.date() != public_holiday_attendance_check:
                            ph_lop += 2
                        # if attend.check_in.date() != self.third_friday_date:
                        #     ph_lop5 += 2
                        for leave in employee_leave_aa:
                            if currentMonth == leave.date_from.month:
                                if leave.request_date_from == public_holiday_attendance_check:
                                    ph_lop_1 += 1
                            if currentMonth == leave.date_from.month and leave.holiday_status_id.name == 'Unpaid':
                                if leave.request_date_from == public_holiday_attendance_check:
                                    ph_lop_11 += 1 / self.employee_present_days
        ph_lop_2 = ph_lop_1 / self.employee_present_days
        ph_lop_3 = ph_lop / self.employee_present_days
        count3 = count / self.employee_present_days

        if count3 == ph_lop_2:
            count1 += 1 - ph_lop_11
            self.public_lop_count_days = count1
            self.employee_loptotal_days += self.public_lop_count_days
        if count3 == ph_lop_3:
            count2 = ph_lop_3 * 1
            self.public_lop_count_days = count2
            self.employee_loptotal_days += self.public_lop_count_days
        if ph_lop_2 > 0 and ph_lop_3 > 0:
            count4 = ph_lop_3 - ph_lop_2 * 2
            if count3 < ph_lop_2 and count < ph_lop:
                self.public_lop_count_days = ph_lop_2 + count4 - ph_lop_11
                self.employee_loptotal_days += self.public_lop_count_days
            if count3 < ph_lop_2 or count < ph_lop:
                self.public_lop_count_days = ph_lop_2 + count4 - ph_lop_11
                self.employee_loptotal_days += self.public_lop_count_days
        non_present = self.total_number_of_days - self.employee_final_present_days
        # self.non_present_days = non_present - self.employee_loptotal_days
        # self.employee_loptotal_days += self.non_present_days

    def employee_attendance_leave(self):
        count = 0.00
        attendance = 0.00
        timeoff_count = 0.00
        public_holiday = 0.00
        public_holiday1 = 0.00
        profitpercent = 0.00
        currentMonth = datetime.now().month
        public_leave_config = self.env['hr.holidays.public'].search([('year_id', '=', self.date_year)])
        unpaid_leave_timeoff = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '=', 'Unpaid'),
             ('state', '=', 'validate')])
        # self.employee_loptotal_days = unpaid_leave_timeoff.number_of_days
        employee_timeoff = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '=', 'Unpaid'),
             ('state', '!=', 'validate')])
        if employee_timeoff:
            for lines in employee_timeoff:
                unpaid_lave_count_days = lines.number_of_days
                if lines.request_date_from == self.third_friday_date:
                    timeoff_count += 1
                for line in self.employee_id.attendance_ids:
                    if lines.request_date_from == self.third_friday_date or line.check_in.date() != self.third_friday_date:
                        attendance += 2
                if self.employee_present_days != 0:
                    self.employee_loptotal_days = unpaid_lave_count_days + (attendance / self.employee_present_days)
        if public_leave_config:
            for public in public_leave_config.line_ids:
                for emp in self.employee_id.attendance_ids:
                    if currentMonth == public.date.month:
                        public_holiday_date = public.date
                        public_leave = public_holiday_date - timedelta(days=1)
                        if public_leave != emp.check_in.date() and public_leave != employee_timeoff.request_date_from:
                            public_holiday += 2
                            try:
                                profitpercent = (public_holiday / self.employee_present_days)
                            except ZeroDivisionError:
                                profitpercent = 0
            self.public_lop_count_days = profitpercent

    def current_employee_attendance(self):
        self.employee_year_month_button()
        if self.employee_id:
            self.get_employee_details()
            employee_attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', self.employee_id.id)])
            # [('employee_id', '=', self.employee_id.id), ('custom_state', '=', 'approve')])
            emp_check_in = []
            emp_check_out = []
            count = 0.00
            non_present_count = 0.00
            present_amount = 0.00
            for attend in employee_attendance:
                if self.date_from and self.date_to:
                    if attend.check_in and not attend.check_out and attend.check_in.month == self.date_from.month:
                        raise ValidationError(
                            _("Alert!,The selected Employee of Mr/Mrs.%s. Attendance has False Value So, Payslip "
                              "can't generate it.\n "
                              "Please check it.") % (
                                self.employee_id.name))
                    if self.date_from.month == attend.check_in.month and self.date_to.month == attend.check_out.month \
                            and attend.check_in.day == attend.check_out.day:
                        count += 1

                present_amount = (self.employee_final_present_days * self.employee_one_day_salary)

            self.write({
                'employee_present_days': count,
                'employee_final_present_days': count})
            if not self.employee_id.bulk_attendance_employee:
                for attend in employee_attendance:
                    if self.date_from and self.date_to:
                        if self.date_from.month == self.date_to.month and attend.check_in.month and attend.check_out.month:
                            count += 1
            else:
                bulk_attendance = self.env['bulk.attendance'].search(
                    [('emp_code', '=', self.employee_id.emp_code), ('month_list', '=', self.date_months),
                     ('year_id', '=', self.date_year)])
                # for entry in bulk_attendance:
                print('--------------------------------------', bulk_attendance.number_of_days)
                count = bulk_attendance.number_of_days
                self.employee_present_days = count
                if count > 0:
                    present_amount = (self.employee_final_present_days * self.employee_one_day_salary)
                else:
                    raise ValidationError(
                        _("Alert !, Selected Employee %s is Bulk Employee Category ,"
                          "So You Must Import the Bulk Attendance.")
                        % (self.employee_id.name))
            if self.total_number_of_days > count:
                self.write({
                    'employee_present_days': count, 'non_present_days': self.total_number_of_days - count,
                    'employee_final_present_days': count,
                    'employee_loptotal_days': self.non_present_days - self.total_balance_days})
            # else:
            #     raise ValidationError(_("The employee Present Days Must be smaller than Total Number of Days"))
            if self.employee_present_days > 0:
                if self.employee_present_days > self.number_working_of_days:
                    raise Warning(
                        _("Alert!,The Employee Present day (%s) must be Equal or Smaller than Number of Working Days (%s).") % (
                            self.employee_present_days, self.number_working_of_days))
                for works in self.worked_days_line_ids:
                    if works.code == 'WORK100':
                        works.write({
                            'number_of_days': self.employee_present_days})
                    elif works.code == 'Unpaid':
                        works.write({
                            'number_of_days': self.number_working_of_days})
                self.write({'amount_net_total': present_amount})
                self.employee_final_present_days = (
                            self.employee_present_days + self.total_balance_days + self.leave_paid_timeoff)

                for netsalary in self.line_ids:
                    if netsalary.category_id.name != 'Deduction' and \
                            netsalary.category_id.name != 'Company Contribution':
                        self.employee_final_present_days = self.leave_paid_timeoff + \
                                                           self.employee_present_days + \
                                                           self.number_of_leave
                        try:
                            profitpercent = (netsalary.amount / self.total_days_of_month)
                            profitpercentage = profitpercent * self.employee_final_present_days
                        except ZeroDivisionError:
                            profitpercent = 0
                            profitpercentage = profitpercent * self.employee_final_present_days
                        netsalary.update({
                            'amount': profitpercentage})
            else:
                raise ValidationError(
                    _("Alert!,The selected Employee of Mr.Mrs.%s, Doesn't have Attendance.SO, Payslip can't generate "
                      "it.") % (
                        self.employee_id.name))

    def employee_birthday_amount(self):
        birthday = self.employee_id.birthday
        from datetime import datetime
        currentMonth = datetime.now().month
        birthday_month = birthday.month
        if currentMonth == birthday_month:
            for bday in self.line_ids:
                if bday.name == 'Birthday Allowance':
                    bday.write({
                        'amount': self.bday_allowance})

    def flight_allowance(self):
        from datetime import datetime
        anniversary = self.employee_id.date_of_joining
        currentDay = datetime.now().day
        currentMonth = datetime.now().month
        import datetime
        datem = datetime.datetime.strptime(str(anniversary), "%Y-%m-%d")
        if datem.month == currentMonth:
            for flight in self.line_ids:
                if flight.name == 'Flight Allowance':
                    flight.write({
                        'amount': self.flt_allowance})

    def advance_salary(self):
        advance_salary_amount = self.env['salary.advance'].search([('employee_id', '=', self.employee_id.id)])
        employee_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        for salary_advance in advance_salary_amount:
            advance_sal = salary_advance.advance
            advance_sal_date = salary_advance.date
            from datetime import datetime
            currentMonth = datetime.now().month
            import datetime
            datem = datetime.datetime.strptime(str(advance_sal_date), "%Y-%m-%d")
            if currentMonth == datem.month:
                for sal in self.line_ids:
                    if sal.name == 'Advance Salary':
                        sal.write({
                            'amount': advance_sal})
                        employee_contract.write({
                            'advance_salary': advance_sal})

    def loan_deduct(self):
        loan_amount_deduction = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id)])
        employee_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        total_paid_amount = 0.00
        balance_amount = 0.00
        for loan in loan_amount_deduction.loan_lines:
            loan_payment_date = loan.date
            from datetime import datetime
            currentMonth = datetime.now().month
            import datetime
            datem = datetime.datetime.strptime(str(loan_payment_date), "%Y-%m-%d")
            # currentMonth = datetime.now().month
            # loan_payment_date = loan.month
            if currentMonth == datem.month:
                for loans in self.line_ids:
                    if loans.name == 'Loan':
                        loans.write({
                            'amount': loan.amount})
                        employee_contract.write({
                            'loan_deduction': loan.amount})
                        total_paid_amount += loan.amount
                        balance_amount -= loan_amount_deduction.balance_amount - loan.amount
                        loan_amount_deduction.write({
                            'total_paid_amount': total_paid_amount})
                        loan_amount_deduction.write({
                            'balance_amount': abs(balance_amount)})

    def _payslip_calculation(self):
        # self.employee_balance_days = self.total_days_of_month - (
        #         self.employee_final_present_days + self.employee_loptotal_days + self.number_of_leave)
        self.employee_balance_days = self.total_days_of_month - (
                self.employee_final_present_days + self.employee_loptotal_days)
        allowance = 0.00
        deduction = 0.00
        flight = 0.00
        birthday = 0.00
        loans = 0.00
        unpaid = 0.00
        adv_sal = 0.00
        total_deduct = 0.00
        net = 0.00
        basic = 0.00
        up = 0.00
        profitpercentdays = 0.00
        # if self.employee_id:
        #     for line in self.line_ids:
        #         if line.category_id.name == 'Deduction' and line.category_id.name != 'Unpaid':
        #             if line.name != 'Unpaid':
        #                 deduction += line.amount
        #                 self.deduction_amount = deduction
        #         if line.category_id.name == 'Basic':
        #             basic += line.amount
        #         if line.category_id.name == 'Allowance':
        #             allowance += line.amount
        #         if line.category_id.name == 'Gross':
        #             line.write({
        #                 'amount': allowance + basic})
        #         if line.name == 'Unpaid':
        #             up += line.amount
        #         if line.category_id.name == 'Net':
        #             if deduction > 0:
        #                 net = (allowance + basic) - (deduction)
        #                 line.write({
        #                     'amount': net})
        #             else:
        #                 net = (allowance + basic)
        #                 line.write({
        #                     'amount': net})
        if self.employee_id:
            for line in self.line_ids:
                try:
                    profitpercentdays = (self.contract_id.wage / self.total_days_of_month)
                except ZeroDivisionError:
                    self.employee_one_day_salary = profitpercentdays
                # self.employee_one_day_salary = self.contract_id.wage / self.total_days_of_month
                if line.category_id.name == 'Deduction' and line.category_id.name != 'Unpaid':
                    if line.name != 'Unpaid':
                        deduction += line.amount
                        self.deduction_amount = deduction
                if line.category_id.name == 'Basic':
                    basic += line.amount
                if line.category_id.name == 'Allowance':
                    allowance += line.amount
                if line.category_id.name == 'Gross':
                    line.write({
                        'amount': allowance + basic})
                if line.name == 'Unpaid':
                    # up += line.amount
                    up = self.employee_balance_days * self.employee_one_day_salary
                    line.write({
                        'amount': up})
                if line.category_id.name == 'Net':
                    if deduction > 0:
                        # net = (allowance + basic) - (deduction)
                        net = (allowance + basic)
                        line.write({
                            'amount': net})
                    else:
                        net = (allowance + basic)
                        line.write({
                            'amount': net})

    def loan_payment(self):
        gross_amount = 0.00
        final_gross_amount = 0.00
        basic_amount = 0.00
        final_basic_amount = 0.00
        hra_amount = 0.00
        final_hra_amount = 0.00
        if self.loan_deduction == True:
            for loan in self.line_ids:
                if loan.name == 'Gross':
                    total_gross = loan.amount * (1 - (self.gross_deduction_amount or 0.0) / 100.0)
                    loan.write({
                        'amount': total_gross})
                if loan.name == 'Basic Salary':
                    total_basic = loan.amount * (1 - (self.basic_deduction_amount or 0.0) / 100.0)
                    loan.write({
                        'amount': total_basic})

    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped('line_ids').filtered(lambda line: line.category_id)

    def _compute_payslip_count(self):
        for payslip in self:
            payslip.payslip_count = len(payslip.line_ids)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(self.filtered(lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(_("Payslip 'Date From' must be earlier 'Date To'."))

    def action_payslip_draft(self):
        return self.write({'state': 'draft'})

    def action_payslip_done(self):
        self.compute_sheet()
        return self.write({'state': 'done'})

    def action_payslip_cancel(self):
        if self.filtered(lambda slip: slip.state == 'done'):
            raise UserError(_("Cannot cancel a payslip that is done."))
        return self.write({'state': 'cancel'})

    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done()
        form_view_ref = self.env.ref('om_om_hr_payroll.view_hr_payslip_form', False)
        tree_view_ref = self.env.ref('om_om_hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': (_("Refund Payslip")),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(tree_view_ref and tree_view_ref.id or False, 'tree'),
                      (form_view_ref and form_view_ref.id or False, 'form')],
            'context': {}
        }

    def check_done(self):
        return True

    # def employee_contract_validate_to_generate(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             employee_contract_valdiate = rec.env['hr.contract'].sudo(). \
    #                 search([('employee_id', '=', rec.employee_id.id)])
    #             if employee_contract_valdiate.start_date_doj:
    #                 if rec.date_from:
    #                     if rec.date_from < employee_contract_valdiate.start_date_doj:
    #                         raise ValidationError(
    #                             _("Alert!, The Employee of Mr.%s, Contract Date Starts from %s, \n"
    #                               " But the selected Date Period is %s. Please check it.") % (
    #                                 rec.employee_id.name, employee_contract_valdiate.start_date_doj, rec.date_from))
    #                 if rec.date_to:
    #                     if rec.date_to < employee_contract_valdiate.start_date_doj:
    #                         raise ValidationError(
    #                             _("Alert!, The Employee of Mr.%s, Contract Date Starts from %s, \n "
    #                               "But the Selected Date Period is %s. Please check it.") % (
    #                                 rec.employee_id.name, employee_contract_valdiate.start_date_doj, rec.date_to))
    #
    #                 if rec.date_from and rec.date_to:
    #                     if rec.date_to < employee_contract_valdiate.start_date_doj:
    #                         raise ValidationError(
    #                             _("Alert!, The Employee of Mr.%s, Contract Date Starts from %s, \n "
    #                               "But the Selected Date Period is %s.Please check it.") % (
    #                                 rec.employee_id.name, employee_contract_valdiate.start_date_doj, rec.date_from,
    #                                 rec.date_to))
    #

    # def payslip_employee_contract_validate_to_generate(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             employee_contract_valdiate = self.env['hr.contract'].sudo(). \
    #                 search([('employee_id', '=', self.employee_id.id)])
    #             if employee_contract_valdiate.amount_settlment_diff != 0:
    #                 raise ValidationError(_("Alert!, Payslip cannot generate for the Employee of Mr.%s, \n"
    #                                         "The Contract Salary Allocation is Not Matching with CTC - %s. "
    #                                         "and The Payment Difference is %s.") % (
    #                                       rec.employee_id.name, employee_contract_valdiate.ctc,
    #                                       employee_contract_valdiate.amount_settlment_diff))

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))
        return super(HrPayslip, self).unlink()

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            if not contract_ids:
                raise ValidationError(
                    _("No running contract found for the employee: %s or no contract in the given period" % payslip.employee_id.name))
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
            payslip.get_employee_details()
            payslip.employee_attendance_leave()
            payslip.current_employee_attendance()
            payslip._payslip_calculation()
            # payslip.payslip_validation_error()
            # payslip.employee_contract_validate_to_generate()
            # payslip.payslip_employee_contract_validate_to_generate()
            # payslip.get_employee_details()
            payslip.employee_birthday_amount()
            payslip.bulk_attendance_of_employee()
            payslip.flight_allowance()
            payslip.loan_payment()
            payslip.loan_deduct()
            payslip.advance_salary()
            payslip.compute_days()
            # payslip.sick_leave_details()
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] -= hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] -= hours / work_hours

            # compute worked days
            work_data = contract.employee_id._get_work_days_data(
                day_from,
                day_to,
                calendar=contract.resource_calendar_id,
                compute_leaves=False,
            )
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                }
                res += [input_data]
        return res

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and \
                                                          localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = contract.company_id.currency_id.round(amount * qty * rate / 100.0)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    if not amount == 0.00:
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
                employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        self.ensure_one()
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
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
        if contracts:
            worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            self.worked_days_line_ids = worked_days_lines

            input_line_ids = self.get_inputs(contracts, date_from, date_to)
            input_lines = self.input_line_ids.browse([])
            for r in input_line_ids:
                input_lines += input_lines.new(r)
            self.input_line_ids = input_lines
            return

    @api.onchange('contract_id')
    def onchange_contract(self):
        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):
        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    slip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade')
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, index=True)
    rate = fields.Float(string='Rate (%)', default=100.0)
    amount = fields.Float()
    quantity = fields.Float(default=1.0)
    total = fields.Float(compute='_compute_total', string='Total')

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'employee_id' not in values or 'contract_id' not in values:
                payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
                values['employee_id'] = values.get('employee_id') or payslip.employee_id.id
                values['contract_id'] = values.get('contract_id') or payslip.contract_id and payslip.contract_id.id
                if not values['contract_id']:
                    raise UserError(_('You must set a contract to create a payslip line.'))
        return super(HrPayslipLine, self).create(vals_list)


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Number of Days')
    number_of_hours = fields.Float(string='Number of Hours')
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
                                  help="The contract for which applied this input")


class HrPayslipInput(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    amount = fields.Float(help="It is used in computation. For e.g. A rule for sales having "
                               "1% commission of basic salary for per product can defined in expression "
                               "like result = inputs.SALEURO.amount * contract.wage*0.01.")
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
                                  help="The contract for which applied this input")


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id', string='Payslips', readonly=True,
                               states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="If its checked, indicates that all payslips generated from here are refund payslips.")

    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    def close_payslip_run(self):
        return self.write({'state': 'close'})

    def done_payslip_run(self):
        for line in self.slip_ids:
            line.action_payslip_done()
        return self.write({'state': 'done'})

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('You Cannot Delete Done Payslips Batches'))
        return super(HrPayslipRun, self).unlink()

    # @api.onchange('slip_ids')
    # def payslip_validate(self):
    #     date_fro = self.date_start
    #     from datetime import datetime
    #     currentMonth = datetime.now().month
    #     import datetime
    #     datem = datetime.datetime.strptime(str(date_fro), "%Y-%m-%d")
    #     pay_date = self.env['hr.payslip']
    #     for pay in pay_date:
    #         if pay.date_from.month == currentMonth:
    #             raise ValidationError(_('The payslip can only be generated once'))
