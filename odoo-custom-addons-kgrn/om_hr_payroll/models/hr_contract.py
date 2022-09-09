# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo.exceptions import Warning, ValidationError, UserError
from odoo import api, fields, models, _


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    ctc = fields.Float(string='CTC')
    wage = fields.Float(string='Basic')
    convenyance_allowance = fields.Float(string='Coveyance Allowance')
    special_allowance = fields.Float(string='Special Allowance')
    house_rent_allowance = fields.Float(string='House Rent Allowance')
    notice_period_pay = fields.Float(string='Notice Period Pay')
    leave_incentives = fields.Float(string='Leave Allowance')
    travel_incentives = fields.Float(string='Travel Allowance')
    health_insurance = fields.Float(string='Health Insurance')
    advance_salary = fields.Float(string="Advance Salary")
    loan_deduction = fields.Float(string="Loan Deduction")
    unpaid_leave_amount_deduction = fields.Float(string="Unpaid Amount Deduction")
    basic_percentage = fields.Float(string='Basic Percentage %')
    conveyence_percentage = fields.Float(string='Coveyance Allowance Percentage %')
    travel_percentage = fields.Float(string='Travel Allowance Percentage %')
    hra_percentage = fields.Float(string='HRA Allowance Percentage %')
    special_alwnance_percentage = fields.Float(string='Special Allowance Percentage %')
    house_allowance = fields.Float(string="HRA Allowance")
    basic_allowance = fields.Float(string="Basic Allowance")
    bday_allowance = fields.Float(string="Birthday Allowance", compute='employee_birthday_amount')
    flt_allowance = fields.Float(string="Flight Allowance", compute='flight_allowance')

    @api.depends('employee_id')
    def employee_birthday_amount(self):
        if self.employee_id and self.bday_allowance == 0:
            birthday = self.employee_id.birthday
            from datetime import datetime
            currentMonth = datetime.now().month
            currentyear = datetime.now().year
            # year_completion = self.employee_id.Employee_one_year_completion.year
            if birthday:
                birthday_month = birthday.month
                # if year_completion >= currentMonth:
                if currentMonth == birthday_month:
                    bday = 500
                    self.bday_allowance = bday
            else:
                bday = 0
                self.bday_allowance = bday

    @api.onchange('employee_id')
    def flight_allowance(self):
        from datetime import datetime
        anniversary = self.employee_id.date_of_joining
        currentDay = datetime.now().day
        currentMonth = datetime.now().month
        # year_completion = self.employee_id.Employee_one_year_completion.month
        import datetime
        # datem = datetime.datetime.strptime(str(anniversary), "%Y-%m-%d")
        if self.employee_id and self.flt_allowance == 0:
            fligth = anniversary.month
            if fligth == currentMonth:
                flight = 700
                self.flt_allowance = flight

    def leave_refuse(self):
        employee_contract = self.env['hr.leave.allocation'].search([('employee_id', '=', self.employee_id.id)])
        for emp in employee_contract:
            join_date = self.employee_id.date_of_joining
            join_month = join_date.month
            currentDay = datetime.now().day
            currentMonth = datetime.now().month
            if join_month == currentMonth:
                for leave in employee_contract:
                    leave.write({'state': 'refuse'})

    @api.onchange('wage', 'hra_percentage', 'basic_percentage')
    def hra_allowance(self):
        for record in self:
            record.wage = False
            record.house_rent_allowance = False
            total_basic = 0.00
            total_conveyance = 0.00
            if record.ctc:
                if record.basic_percentage:
                    total_basic = record.ctc * (1 - (record.basic_percentage or 0.0) / 100.0)
                    record.write({
                        'basic_allowance': total_basic})
                    record.wage = record.ctc - record.basic_allowance
            if record.wage > 0.00:
                if record.hra_percentage:
                    total_conveyance = record.wage * (1 - (record.hra_percentage or 0.0) / 100.0)
                    record.write({
                        'house_allowance': total_conveyance})
                    record.house_rent_allowance = record.wage - record.house_allowance

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        for contract in self:
            if active:
                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0


class HrContractAdvantageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    lower_bound = fields.Float('Lower Bound', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage')
