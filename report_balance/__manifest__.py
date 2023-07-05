# -*- coding: utf-8 -*-
{
    'name': 'Balance Pruebas',
    'summary': '''
        View and create reports
    ''',
    'description': '''
        - Blance de pruebas con cuenta analitica.
    ''',
    'author': '1-800CLOUD',
    'website': 'https://1-800cloud.com',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'version': '15.0.0.0.4',
    'depends': [
        'base_setup',
        'account_report',
        'account_ifrs',
        'report_xlsx',
        'account_baseline',
        'account',
        'account_report',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/balance_report.xml',
        'reports/reports.xml',
        'templates/internal_layout.xml',
        'templates/template_account_balance.xml',
        'wizard/account_balance.xml',
    ],
}