# -*- coding: utf-8 -*-
{
    'name': 'Stock Agromark',
    'summary': '''
        Inventario Agromark
    ''',
    'description': '''
        - Reporte de disponibilidad de inventario
    ''',
    'author': '1-800CLOUD',
    'website': 'http://www.1-800cloud.com',
    'category': 'Inventory/Inventory',
    'license': 'LGPL-3',
    'version': '15.0.0.0.0',
    'depends': [
        'stock',
        'sale',
        'product_brand'
    ],
    'data': [
        # 'security/ir.model.access.csv',
         'reports/stock_report.xml',
         'views/menuitems.xml',
    ],
}
