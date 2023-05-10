# -*- coding: utf-8 -*-
{
    'name': "Account Report Agromark",
    'summary': """
        Extensión para Reportes Agromark.\n
    """,
    'description': """
        - Se agrega opción para poder generar PDF de reporte de auxiliar de facturas.
    """,
    'author': "1-800CLOUD",
    'contributors': [
        "Fernando Fernandez <nffernandezm@gmail.com>"
    ],
    'website': "https://1-800cloud.com/",
    'license': 'OPL-1',
    'category': 'Account/Report',
    'version': '15.0.0.1.7',
    'depends': [
        'account_report',
    ],
    'data': [
        'report/reports.xml',
        'templates/account_auxiliary_invoices_template.xml',
        'wizard/account_auxiliary_invoices_wizard_view.xml',
        'wizard/account_auxiliary_wizard_view.xml',
        'wizard/account_balance_wizard_view.xml',
        
    ]
}
