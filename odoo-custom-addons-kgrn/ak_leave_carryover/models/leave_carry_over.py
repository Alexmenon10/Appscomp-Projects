# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from datetime import date
import time
from datetime import timedelta, datetime
import datetime


class CarryOver(models.Model):
    _name = 'leave.carry.over'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Carry Over'
    _order = 'id desc'

    name = fields.Char('Description', required=True)
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    source_leave_type_id = fields.Many2one(
        comodel_name='hr.leave.type',
        relation='source_leave_type_carryover_rel',
        string="Carry Over From",
        required=True,
        help="The time off type that has expired/is to expire, and from which you wish to carry over leave from."
    )
    dest_leave_type_id = fields.Many2one(
        comodel_name='hr.leave.type',
        relation='dest_leave_type_carryover_rel',
        string="Carry Over To",
        required=True,
        help='''The new time off type that will remain valid for the upcoming period. This
        time off type will be selected in the time off allocations generated from this carry over transaction.'''
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'State', default='draft', required=True, tracking=True)
    carryover_method = fields.Selection([
        ('balance', 'Carry Over Balance'),
        ('percentage', 'Carry Over a Percentage of Balance')],
        'Carry Over Method',
        default='balance',
        required=True,
        help='''Carry Over Balance: The carry over will move forward all time
                off balances from the last period to the new period\n''')
    carryover_percentage = fields.Integer('Carry Over Percentage %', store=True)
    limit_carryover = fields.Boolean(
        string="Limit Carryover",
        help="Select to enforce a limit/maximum number of days to be carried over to the new period.")
    carryover_days = fields.Float('Max Days to Carry Over')
    carryover_executed = fields.Boolean('Carry Over Executed?', default=False, copy=False)
    schedule_carryover = fields.Boolean('Schedule Carry Over?')
    scheduled_date = fields.Date(
        string='Scheduled Date',
        copy=False,
        help="A scheduled action will execute this carry over on this date. Balances will be considered as of the scheduled date."
    )
    allocations_count = fields.Integer(compute="_compute_allocations_count")
    carrry_over_leave_count = fields.Integer(string='Carry Over Leave')
    allocations_generated = fields.Boolean('Allocations Generated', default=False, copy=False)
    actual_carry_over_remarks = fields.Text(string='Employee Leave Carry over Remarks')
    employee_carryover = fields.Many2one('hr.employee', string='Employee Carry over')

    def update_employee_carryover(self):
        for rec in self.employee_ids:
            if rec.carry_over == True:
                rec.write({
                    'actual_carry_over_leave': False,
                    'approved_leave': False,
                    'internal_leave_deduction': False,
                    'actual_carry_over_remarks': False,
                    'carry_over': False,
                })

    @api.onchange('carryover_method')
    def onchange_emp_no(self):
        if self.carryover_method == 'balance':
            self.write({
                'limit_carryover': True,
            })
        else:
            self.write({
                'limit_carryover': False,
            })

    def get_employee(self):
        employee_details = self.env['hr.employee'].search([('name', '=', self.employee_ids.name)])
        if self.carryover_method == 'percentage':
            employee_details.write({
                'carry_over': True,
                'actual_carry_over_remarks': self.actual_carry_over_remarks,
                'actual_carry_over_leave': employee_details.remaining_leaves,
                'approved_leave': self.carrry_over_leave_count,
            })
            deduction = (employee_details.actual_carry_over_leave - employee_details.approved_leave)
            employee_details.write({
                'internal_leave_deduction': deduction,
            })
        else:
            employee_details.write({
                'carry_over': True,
                'actual_carry_over_remarks': self.actual_carry_over_remarks,
                'actual_carry_over_leave': employee_details.remaining_leaves,
                'approved_leave': self.carryover_days,
            })
            deduction = (employee_details.actual_carry_over_leave - employee_details.approved_leave)
            employee_details.write({
                'internal_leave_deduction': deduction,
            })

    def get_contract(self):
        contract_details = self.env['hr.contract'].search([('employee_id', '=', self.employee_ids.name)])
        contract_details.leave_refuse()

    def _compute_allocations_count(self):
        LeaveAllocation = self.env['hr.leave.allocation']
        self.allocations_count = LeaveAllocation.search_count(
            [('leave_carryover_id', '=', self.id)]
        )

    def get_allocations_records(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocations',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave.allocation',
            'domain': [('leave_carryover_id', '=', self.id)],
        }

    def generate_notification(self, title, message):
        self.env['bus.bus'].sendone(
            (self._cr.dbname,
             'res.partner',
             self.env.user.partner_id.id),
            {
                'type': 'simple_notification',
                'sticky': False,
                'warning': True,
                'title': _(title),
                'message': _(message)})

    def calculate_balance(self, employee):
        # get all allocations
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('holiday_status_id', '=', self.source_leave_type_id.id)
        ])
        allocations_days = sum(allocations.mapped('number_of_days'))
        # get all approved requests
        leave_requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['validate']),
            ('holiday_status_id', '=', self.source_leave_type_id.id)
        ])
        leave_request_days = sum(leave_requests.mapped('number_of_days'))
        # calculcate leave balance
        balance_days = allocations_days - leave_request_days
        # if a percentage method was used:
        if self.carryover_method == 'percentage':
            balance_days = balance_days * (self.carryover_percentage / 100)
            self.carrry_over_leave_count = balance_days
        return balance_days

    def employee_carry_over_approve_remarks(self):
        view_id = self.env['employee.carry.over.approve.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Leave Carry over Remarks',
            'res_model': 'employee.carry.over.approve.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('ak_leave_carryover.employee_carry_over_approve_remarks_wizard', False).id,
            'target': 'new',
        }

    def create_leave_allocations(self, carryover_id, leave_type, employee, days):
        carryover_record = self.env['hr.leave.allocation'].create({
            'leave_carryover_id': carryover_id,
            'state': 'draft',
            'name': f'{leave_type.name} - Carry Over Allocation for {employee.name}',
            'holiday_status_id': leave_type.id,
            'holiday_type': 'employee',
            'employee_id': employee.id,
            'number_of_days': days,
            'allocation_type': 'regular',
        })

    def generate_carryover(self):
        if len(self.employee_ids) > 0:
            if self.state != 'scheduled' and self.schedule_carryover and self.scheduled_date:
                self.write({
                    'state': 'scheduled',
                })
                self.generate_notification('Carry Over Scheduled',
                                           f'This carry over has been scheduled to run on {str(self.scheduled_date)}.')
                return
            if self.limit_carryover:
                for employee in self.employee_ids:
                    e_carryover_days = self.calculate_balance(employee)
                    if e_carryover_days <= 0:
                        continue
                    if e_carryover_days > self.carryover_days:
                        e_carryover_days = self.carryover_days
                    self.create_leave_allocations(self.id, self.dest_leave_type_id, employee, e_carryover_days)
            else:
                for employee in self.employee_ids:
                    e_carryover_days = self.calculate_balance(employee)
                    if e_carryover_days <= 0:
                        continue
                    self.create_leave_allocations(self.id, self.dest_leave_type_id, employee, e_carryover_days)
            carryover_allocations = self.env['hr.leave.allocation'].search(
                [('leave_carryover_id', '=', self.id)])
            self.allocations_generated = True
            if len(carryover_allocations) == 0:
                self.generate_notification('No Balance',
                                           'No leave balance found for any of the selected employees. You may update the employees list and try again.')
            else:
                self.write({
                    'carryover_executed': True
                })
                self.generate_notification('Allocations created',
                                           'Carry over allocations are created and are in a draft state. You can review them and validate this carry over record once reviewed.')
        else:
            raise UserError(
                _('You need to select at least 1 employee before validating this carry over transaction'))

    def re_generate_carryover(self):
        carryover_allocations = self.env['hr.leave.allocation'].search(
            [('leave_carryover_id', '=', self.id)])
        # if self.carryover_executed == True:
        carryover_allocations.unlink()
        self.generate_carryover()
        # else:
        #     raise ValidationError(_('Alert No Balance'
        #           ' \n No leave balance found for any of the selected employees'))

    def confirm_carryover(self):
        carryover_allocations = self.env['hr.leave.allocation'].search(
            [('leave_carryover_id', '=', self.id)])
        if len(carryover_allocations) > 0:
            for rec in carryover_allocations:
                rec.update({
                    'state': 'validate'
                })
            self.generate_notification('Allocations Validated',
                                       'Carry Over is complete. All allocations created from this Carry Over record were validated.')
            self.write({
                'state': 'done'
            })
        else:
            self.generate_notification('No Balance',
                                       'No leave balance found for any of the selected employees, and no carry over allocations were created. You may cancel this record.')

    def cancel_carryover(self):
        carryover_allocations = self.env['hr.leave.allocation'].search(
            [('leave_carryover_id', '=', self.id)])
        if len(carryover_allocations) > 0:
            for rec in carryover_allocations:
                rec.unlink()
            self.generate_notification('Allocations Deleted',
                                       'All allocations created from this Carry Over record were deleted.')
        self.write({
            'carryover_executed': False,
            'state': 'cancel',
            'allocations_generated': False
        })

    def reset_to_draft(self):
        self.write({
            'state': 'draft'
        })

        # @api.model

    def process_scheduled_carryover(self):
        current_date = fields.Date.context_today(self)
        scheduled_carryovers = self.search([
            ('state', '=', 'scheduled')
        ])
        for carryover in scheduled_carryovers:
            if carryover.scheduled_date:
                if carryover.scheduled_date <= current_date:
                    carryover.generate_carryover()
                    carryover.confirm_carryover()
        return True

        # @api.constrains('dest_leave_type_id', 'source_leave_type_id')
        # def _check_duplication(self):
        #     if self.dest_leave_type_id == self.source_leave_type_id:
        #         raise ValidationError(
        #             _("You cannot select the same time off type in both the 'From' and 'To' fields."))

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        current_date = fields.Date.context_today(self)
        if self.state == 'draft' and self.scheduled_date:
            if self.scheduled_date <= current_date:
                raise ValidationError(
                    _("Invalid Scheduled Date"))

    @api.constrains('carryover_percentage')
    def _check_carryover_percentage(self):
        if self.carryover_percentage:
            if self.state == 'draft':
                if self.carryover_percentage < 1 or self.carryover_percentage > 100:
                    raise ValidationError(
                        _("Invalid Carry Over Percentage"))

    def unlink(self):
        if self.state != 'draft':
            raise UserError(
                'You can only delete carry over records that are in a draft state.'
            )
        return super(CarryOver, self).unlink()


class EmployeeLeaveCarryoverRemarks(models.TransientModel):
    _name = 'employee.carry.over.approve.remarks'
    _description = 'Employee Leave Carry over Remarks'
    _inherit = ['mail.thread']

    remarks = fields.Text('Remarks')

    def tick_ok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['leave.carry.over'].search([('id', '=', applicant_id)])
        # active_id1 = self.env['hr.employee'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        current_user = self.env.user.name
        if active_id.state == 'draft':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.update_employee_carryover()
            active_id.get_contract()
            active_id.confirm_carryover()
            active_id.write({
                'actual_carry_over_remarks': text,
            })
            active_id.get_employee()
        return True
