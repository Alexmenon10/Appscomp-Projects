from odoo import fields, models, api, _


class Leave(models.Model):
    _name = 'leave.description.master'
    _description = 'Leave Description Master'

    name = fields.Char(string="Leave")
    date = fields.Date(string="Date")
    days = fields.Float(string="Days", compute='get_leave_details')





class PuclicLeave(models.Model):
    _inherit = 'hr.holidays.public'
    _description = 'Public Holiday'

    year_id = fields.Many2one('hr.payroll.year', string='Year', required='1')

    # def attendance_leave(self):
    #     attendance_approve = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id)])
    #
    #




