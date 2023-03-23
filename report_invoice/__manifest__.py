# -*- coding: utf-8 -*-
{
    'name': 'Invoice Report',
    'summary': '''
        View and create reports
    ''',
    'description': '''
        - report invoices.
    ''',
    'author': '1-800CLOUD',
    'website': 'https://1-800cloud.com',
    'category': 'sales/sale',
    'license': 'LGPL-3',
    'version': '15.0.0.0.0',
    'depends': [
        'base_setup',
        'account_baseline',
        'account',
    ],
    'data': [
        #'security/ir.model.access.csv',
        'reports/report_invoice.xml',
        'views/menuitem_views.xml',
    ],
    'installable': True,
}