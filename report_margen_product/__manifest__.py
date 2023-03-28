# -*- coding: utf-8 -*-
{
    'name': 'Report Margen',
    'summary': '''
        View and create reports
    ''',
    'description': '''
        - report Margen de productos.
    ''',
    'author': '1-800CLOUD',
    'website': 'https://1-800cloud.com',
    'category': 'sales/sale',
    'license': 'LGPL-3',
    'version': '15.0.0.0.0',
    'depends': [
        'product_brand',
        'Stock_Agromark',
        'stock',
        'sale'
    ],
    'data': [
        #'security/ir.model.access.csv',
        'reports/report_margen.xml',
        'views/menuitem_views.xml',
    ],
    'installable': True,
}