# -*- coding: utf-8 -*-
################################################################################# 
#
#    Author: Abdullah Khalil. Copyrights (C) 2021-TODAY reserved. 
#
#    You may use this app as per the rules outlined in the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3. 
#    See <http://www.gnu.org/licenses/> for more detials.
#
################################################################################# 

{
    'name': "CRM Module Extended",
    'summary': "CRM Module Extended",
    'description': """
        Easily manage and schedule your Leads and opportunity with this app.
    """,
    'author': "Appscomp",
    'website': "http://www.appscomp.com",
    'category': 'CRM Category',
    'version': '14.0.0.1',
    'depends': ['mail', 'crm', 'sale', 'sale_crm', 'sales_team', 'project', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/sheduled_action.xml',
        'wizard/partner_statement_view.xml',
        'wizard/excess_time_spent_task_view.xml',
        'views/crm_extended_view.xml',
        'views/project_task_view.xml',
        'views/import_attendance_view.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
}
