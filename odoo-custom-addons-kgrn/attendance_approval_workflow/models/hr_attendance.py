# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields , api , exceptions, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  compute='_onchange_employee_code', required=True,
                                  ondelete='cascade', index=True, store=True)
    custom_state = fields.Selection([
        ('draft', 'New'),
        ('approve', 'Approved'),
        ('reject', 'Rejected')], 
        string='Status', 
        required=True, 
        readonly=True, 
        copy=False, 
        default='draft'
    )
    custom_approver_id = fields.Many2one(
        'res.users',
        string='Approved by', 
        readonly=True, 
        copy=False,
    )
    custom_reject_id = fields.Many2one(
        'res.users', 
        string='Rejected by',
        readonly=True,
        copy=False,
    )
    custom_reason_refuse = fields.Text(
        string='Reason for Reject',
        required=False,
        copy=False,
        readonly=True, 
    )
    emp_code = fields.Char(string='Employee ID')
    bulk_attendance_employee = fields.Boolean(string="Bulk Attendance", help="Bulk Attendance", related='employee_id.bulk_attendance_employee')


    @api.depends('emp_code')
    @api.onchange('emp_code')
    def _onchange_employee_code(self):
        for vals in self:
            emp_id = self.env['hr.employee'].search([('emp_code', '=', vals.emp_code)])
            for val in emp_id:
                empl_name = val.id
            vals.employee_id = empl_name

    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for vals in self:
            if vals.employee_id:
                employee_id = self.env['hr.employee'].search([('name', '=', vals.employee_id.name)])
                for val in employee_id:
                    code = val.emp_code
                vals.emp_code = code

    @api.constrains('check_in', 'check_out', 'employee_id')
    @api.depends('employee_id', 'check_in', 'check_out')
    @api.onchange('employee_id', 'check_in', 'check_out')
    def _check_validity(self):
        if self.employee_id.bulk_attendance_employee:
            raise exceptions.ValidationError(
                _("Cannot create new attendance record for %(empl_name)s, the employee was Add to Bulk Attendance List") % {
                    'empl_name': self.employee_id.name})
        return super(HrAttendance, self)._check_validity()
    def action_approve(self):
        self.write({
            'custom_state': 'approve',
            'custom_approver_id': self.env.uid
        })
    def action_reject(self):
        self.write({
            'custom_state': 'reject'
        })

    def action_draft(self):
        self.write({
            'custom_state': 'draft'
        })