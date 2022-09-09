# -*- coding:utf-8 -*-

{
    'name': 'Odoo 14 HR Payroll',
    'category': 'Generic Modules/Human Resources',
    'version': '14.0.5.0.0',
    'sequence': 1,
    'author': 'Odoo Mates, Odoo SA',
    'summary': 'Payroll For Odoo 14 Community Edition',
    'live_test_url': 'https://www.youtube.com/watch?v=0kaHMTtn7oY',
    'description': "",
    'website': 'https://www.odoomates.tech',
    'depends': [
        'hr_contract',
        'hr_holidays',

    ],
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_sequence.xml',
        'wizard/hr_payroll_payslips_by_employees_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payroll_report.xml',
        'views/header_footer.xml',
        'data/hr_payroll_data.xml',
        'wizard/hr_payroll_contribution_register_report_views.xml',
        'wizard/hr_payroll_excel_report.xml',
        'wizard/time_off_statement.xml',
        'wizard/employee_timesheet_excel_report.xml',
        'views/res_config_settings_views.xml',
        'views/report_contribution_register_templates.xml',
        'views/report_payslip_templates.xml',
        'views/report_payslip_details_templates.xml',
        # 'views/report/payslip.xml',
        'views/report/vitmed_payslip_report.xml',
        'views/employee_leave.xml',
        'views/hr_timeoff.xml'

    ],
    'images': ['static/description/banner.png'],
    'application': True,
}
