# -*- coding: utf-8 -*-
{
    'name': 'Account Voucher Agromark',
    'summary': '''
        Account Voucher Agromark
    ''',
    'description': '''
        - Formato comprobante contable personalizado.
    ''',
    'author': '1-800CLOUD',
    'website': 'http://www.1-800cloud.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Accounting',
    'version': '15.0.0.0.1',
    'depends': [
        'account_voucher'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/generic_accounting_receipt_template.xml',
    ],
}
