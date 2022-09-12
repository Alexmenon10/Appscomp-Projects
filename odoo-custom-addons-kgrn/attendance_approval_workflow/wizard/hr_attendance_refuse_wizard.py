# -*- coding: utf-8 -*-

import datetime 

from odoo import models, fields , _
from odoo.exceptions import UserError


class AccountMoveRefuseWizard(models.TransientModel):
    _name = 'custom.hr.attendance.refuse.wizard'
    _description = 'custom.hr.attendance.refuse.wizard'

    custom_reason = fields.Text(
        string='Reason for Reject',
        required=True,
        copy=True,
    )

    def action_refuse_approval(self):
        attendance_id = self.env['hr.attendance'
            ].browse(self._context.get('active_ids'))
        attendance_id.write({
            'custom_reason_refuse' : self.custom_reason,
            'custom_reject_id': self.env.uid,
            'custom_state': 'reject'
                })
        group_msg = _('Your Entry has been Rejected')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
