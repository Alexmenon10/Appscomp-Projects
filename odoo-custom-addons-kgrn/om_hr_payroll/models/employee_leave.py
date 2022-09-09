from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import timedelta, date, datetime
from datetime import date, timedelta


class EmployeeLeaveEligible(models.Model):
    _name = 'employee.leave.eligible'
    _description = 'Employee Leave Eligible'

    employee_id = fields.Many2one('hr.employee', string="Employee ")
    leave_eligible = fields.Boolean(string='Leave Eligible ')
    leave_type = fields.Many2one('hr.leave.type', string="leave Types")
    annual_leave = fields.Float(string="Annual Leave")
    bereavement_leave = fields.Float(string="Bereavement Leave")
    sick_time_off = fields.Float(string="Sick Time Off")
    compensatory_leave = fields.Float(string="Compensatory Leave")
    study_leave = fields.Float(string="Study Leave")
    casual_leave = fields.Float(string="Casual/ Personal Leave")
    maternity_leave = fields.Float(string="Maternity Leave")
    parental_leave = fields.Float(string="Parental Leave")

    class HrLeave(models.Model):
        _inherit = "hr.leave"


    def action_confirm(self):
        self.employee_leave_eligible()
        # if self.employee_id.remaining_leaves  > 0.00:
        #     raise ValidationError(('Alert!, Mr.%s - Your not Eligable To create Leave for %s,\n Please contact your Manger') %
        #                           (self.employee_id.name, self.holiday_status_id.name))
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})
        holidays = self.filtered(lambda leave: leave.validation_type == 'no_validation')
        if holidays:
            # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
            holidays.sudo().action_validate()
        self.activity_update()
        return True

    def action_approve(self):
        self.employee_leave_eligible()
        # if self.employee_id.remaining_leaves <= 0.00:
        #     raise ValidationError(
        #         ('Alert!, Mr.%s - Your not Eligable To create Leave for %s,\n Please contact your Manger') %
        #         (self.employee_id.name, self.holiday_status_id.name))
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    is_eligible = fields.Boolean(string="IS Eligible")
    today = date.today()

    def employee_leave_eligible(self):
        if self.employee_id:
            if self.employee_id.leave_eligible_date <= self.today:
                self.write({
                    'is_eligible': True})
            else:
                raise ValidationError(('Alert!, Mr.%s - Your not Eligable for %s') %
                                      (self.employee_id.name, self.holiday_status_id.name))

    def employee_dates(self):
        join_date = self.employee_id.date_of_joining
        join_month = join_date.month
        currentDay = datetime.now().day
        currentMonth = datetime.now().month
        if join_month == currentMonth:
            for leave in self:
                leave.write({'state': 'refuse'})


    def action_confirm(self):
        self.employee_leave_eligible()
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Allocation request must be in Draft state ("To Submit") in order to confirm it.'))
        res = self.write({'state': 'confirm'})
        self.activity_update()
        return res

    def action_approve(self):
        self.employee_leave_eligible()
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Allocation request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id

        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        self.activity_update()


