# -*- coding: utf-8 -*-
{
    'name': 'Reporte auxiliar',
    'summary': '''
        View and create reports
    ''',
    'description': '''
        - Auxiliar con cuenta analitica.
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
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/auxiliary_account.xml',
        'reports/reports.xml',
        'templates/internal_layout.xml',
        'templates/template_account_auxiliary.xml',
        'wizard/account_auxiliary.xml',
    ],
}