# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.
{
    'name': 'Attendance Approval Workflow',
    'version': '2.1.3',
    'price': 9.0,
    'depends': [
        'hr_attendance','appscomp_hr','bi_import_employee','ohrms_loan',
    ],
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Human Resources/Attendances',
    'summary':  """This app allows your user to approve workflow on Attendance.""",
    'description': """
This app allows your user to approve reject workflow on Attendance.
    """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'images': ['static/description/image1.png'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hr_attendance_refuse_wizard_view.xml',
        'wizard/hr_attendance_approve_wizard_view.xml',
        'wizard/attendance_import_wizard.xml',
        'views/hr_attendance_view.xml',
        'views/import_attendance_view.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
