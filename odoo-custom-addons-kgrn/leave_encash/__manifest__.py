# -*- coding: utf-8 -*-

{
    'name': 'Human Resource Solution',
    'category': 'HR',
    'description': """
                   HR provides a complete solution for services related to Human Resources and it's relevant perspectives.
                 """,
    'summary': 'Manage Employee Leave Encashment',
    'author': 'Arunagiri K',
    'website': 'http://www.acespritech.com',
    'version': '14.0',
    'depends': ['base', 'om_hr_payroll', 'hr', 'hr_attendance',
                'hr_contract','hr_holidays'],
    'data': [
        #leave encashment
        'security/leave_security.xml',
        'security/ir.model.access.csv',
        'views/hr_job_views.xml',
        'wizard/leave_encash_process_views.xml',
        'views/leave_config_setting_views.xml',
        'views/leave_encash_views.xml',
        'views/hr_payroll_views.xml',
        'views/hr_payroll_data.xml',
        #~ 'views/report.xml',
        #~ 'wizard/leave_encash_report_wizard.xml',
        #~ 'report/leave_encash_report.xml',
        
      
    ],
    'demo': [],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}

