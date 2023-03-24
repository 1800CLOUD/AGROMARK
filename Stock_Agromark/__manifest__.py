# -*- coding: utf-8 -*-
{
    'name': 'Stock Agromark',
    'summary': '''
        Inventario Agromark
    ''',
    'description': '''
        - Base de impuestos sin considerar descuento en compras y facturas proovedor.
    ''',
    'author': '1-800CLOUD',
    'website': 'http://www.1-800cloud.com',
    'category': 'Inventory/Inventory',
    'license': 'LGPL-3',
    'version': '15.0.0.0.0',
    'depends': [
        'stock',
        'sale'
    ],
    'data': [
        # 'security/ir.model.access.csv',
         'views/stock_quant.xml',
         'wizard/stock_quantity_history.xml',
    ],
}
