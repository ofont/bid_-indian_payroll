# -*- coding: utf-8 -*-
{
    'name': 'Odoo Indian Payroll',
    'version': '12.0',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'www.pragtech.co.in',
    'category': 'Human Resources Payroll',
    'summary': 'Odoo Indian Payroll odoo payroll management system odoo payroll management system payroll management payroll app',
    'description': """
Odoo Indian Payroll
===================    
<keywords>
Payroll
odoo payroll
payroll management system
odoo payroll management system
payroll management 
payroll app
       """,
    'depends': ['base', 'hr', 'hr_payroll', 'hr_contract', 'l10n_in_hr_payroll',
                'hr_expense', 'hr_attendance', 'hr_timesheet', 'hr_recruitment', 'hr'],
    'data': [
        'views/hr_payroll_view.xml',
        'views/hr_employee_view.xml',
        'views/settings.xml',
        'views/menuitem.xml',
        'views/complaints.xml',
        'views/hr.xml',
        'views/expense.xml',
        'views/timesheets.xml',
        'views/attendance.xml',
        'views/appraisal_view.xml',
        'views/email_template_complaints.xml',
        'views/email_template_expense.xml',
        'views/email_template_leaves.xml',
        'views/email_template_job_reference.xml',
        'views/hr_leaves.xml',
        'views/appraisal_view.xml',
        'views/recruitment.xml',
        'views/policy_docs.xml',
        'views/timesheets.xml',
        'views/report_payslip.xml',
        'views/payslip_batches_report.xml',
        'views/hr_config_view.xml',
        'views/hr_contract_view.xml',
        'views/monthly_gross_report.xml',
        'security/hr_security.xml',
        'data/email_template.xml',
        'data/wish_cronjob.xml',
        'security/ir.model.access.csv'
    ],
    'images': ['static/description/Animated-indian-payroll.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=310&name=support-odoo-indian-payroll',
    'installable': True,
    'auto_install': False,
}
