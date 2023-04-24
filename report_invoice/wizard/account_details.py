# -*- coding: utf-8 -*-

import json
from json import dumps

from odoo import _, api, fields, models


class AccountDetails(models.TransientModel):
    _name = 'invoice.detail.wizard'
    _description = 'Detailed Invoices Report'

    date_start = fields.Date(
        'Fecha Inicio',
        required=True,
        default=fields.Date.today
    )
    date_end = fields.Date(
        'Fecha Fin',
        required=True,
        default=fields.Date.today
    )

    moves_ids = fields.Many2many('account.move')
    move_type = fields.Selection(
        selection=[
            ('out_invoice', 'Facturas de venta'),
            ('out_refund', 'Notas Credito'),
            ('in_invoice', 'Facturas de Compra'),
            ('in_refund', 'Nota Credito Compra'),
        ],
        default='out_invoice',
        string='Tipo de Factura',
        required=True
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user
    )

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and self.date_end and self.date_end < self.date_start:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_end and self.date_end < self.date_start:
            self.date_start = self.date_end

    def generate_report(self):
        Move = self.env['account.move']
        move_domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', self.move_type),
            ('fe_datetime_invoice', '>=', self.date_start),
            ('fe_datetime_invoice', '<=', self.date_end),
        ]
        moves = Move.search(move_domain)
        self.moves_ids = moves

        report = self.env.ref(
            'report_invoice.action_report_invoice_details_wizard'
        )
        return report.report_action(self)

    def invoice_payments_widget(self, move):
        widget = move.invoice_payments_widget
        payments = json.loads(widget)
        return payments and payments.get('content', []) or []

    def tax_totals_json(self, move):
        widget = move.tax_totals_json
        widget_json = json.loads(widget)
        subtotals = widget_json.get('subtotals')
        groups_by_subtotal = widget_json.get('groups_by_subtotal')
        return subtotals and groups_by_subtotal.get(subtotals[0].get('name')) or []
