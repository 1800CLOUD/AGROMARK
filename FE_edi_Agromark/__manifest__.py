# -*- coding: utf-8 -*-
{
    'name': 'Extensión de Factura Electrónica Agromark',
    'summary': '''
        Extensión de factura electrónica para Agromark.
    ''',
    'description': '''
        - Formato factura de Agromark.
    ''',
    'author': '1-800CLOUD',
    'website': 'https://www.1-800cloud.com',
    'contributors': [' Diego Castaño <diego.castano@1-800cloud.com>'],
    'category': 'Accounting/Localizations/EDI',
    'license': 'OPL-1',
    'version': '15.0.0.0.3',
    'depends': [
        'l10n_co_bloodo'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'reports/account_move_templates.xml',
        # 'views/templates.xml',
    ],
}
