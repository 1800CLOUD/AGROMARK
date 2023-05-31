# -*- coding: utf-8 -*-
{
    'name': 'Report journal',
    'summary': '''
        Auditoria de Diarios
    ''',
    'description': '''
        - 
    ''',
    'author': '1-800CLOUD',
    'website': 'http://www.1-800cloud.com',
    'category': 'account/accountant',
    'license': 'LGPL-3',
    'version': '15.0.0.0.0',
    'depends': [
        'base_setup',
        'account',
    ],
    'data': [
         'security/ir.model.access.csv',
         'reports/report_journal.xml',
         'views/menuitems.xml',
    ],
}
