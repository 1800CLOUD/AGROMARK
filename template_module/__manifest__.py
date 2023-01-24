# -*- coding: utf-8 -*-
{
    'name': 'Helpdesk Strong Machine SAS',
    'summary': '''
        Helpdesk module extension for Strong Machine company.    
    ''',
    'description': '''
        - Web form extension with supplemental fields.
    ''',
    'author': '1-800CLOUD',
    'website': 'https://www.1-800cloud.com',
    'category': 'Services/Helpdesk',
    'license': 'OPL-1',
    'version': '15.0.0.0.1',
    'depends': [
        'helpdesk'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
}
