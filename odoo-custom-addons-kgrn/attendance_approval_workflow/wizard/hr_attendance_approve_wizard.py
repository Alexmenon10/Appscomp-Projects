# -*- coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class HrAttendanceApprove(models.TransientModel):
    _name = 'hr.attendance.approve'
    _description = "Wizard - Attendance Approve/Reject"

    def approve_attendance(self):
        attendances = self._context.get('active_ids')
        attendance_ids = self.env['hr.attendance'].browse(attendances).\
            filtered(lambda x: x.custom_state == 'draft')
        for attendance in attendance_ids:
            attendance.action_approve()

    def reject_attendance(self):
        attendances = self._context.get('active_ids')
        attendance_ids = self.env['hr.attendance'].browse(attendances)
        for attendance in attendance_ids:
            try:
                attendance.action_reject()
            except:
                pass





