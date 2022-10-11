# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Timesheet PDF Report',
    'version': '15.0.1.0.0',
    "category": "Generic Modules/Human Resources",
    'sequence': 25,
    'summary': 'Timesheet PDF Report of Employees',
    'description': 'Timesheet PDF Report of Employees',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'hr_timesheet'],
    'data': [
             'security/ir.model.access.csv',
             'report/timesheet_reports.xml',
             'report/timesheet_templates.xml',
             'report/pending_task_view.xml',
             'report/project_report_template.xml',
             'report/project_base_template.xml',
             'wizard/timesheet_report_views.xml',
             'wizard/project_timesheet_report.xml',
             'wizard/task_pending_wizard.xml',
             'wizard/project_based_report.xml',
            ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
