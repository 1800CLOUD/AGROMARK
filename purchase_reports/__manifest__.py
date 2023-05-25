# -*- coding: utf-8 -*-
{
    'name': 'Purchase Report',
    'summary': '''
        Compras Agromark
    ''',
    'description': '''
        - 
    ''',
    'author': '1-800CLOUD',
    'website': 'http://www.1-800cloud.com',
    'category': 'Purchase/Purchase',
    'license': 'LGPL-3',
    'version': '15.0.0.0.6',
    'depends': [
        'base_setup',
        'purchase',
        'account',
    ],
    'data': [
        # 'security/ir.model.access.csv',
         'reports/purchase_report.xml',
         'views/menuitems.xml',
    ],
}
