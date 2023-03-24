# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

REPORT_TYPE = {
    'local': 'Local',
    'ifrs': 'NIIF'
}

_logger = logging.getLogger(__name__)


class AccountauxiliaryInvoicesWizard(models.Model):
    _inherit = 'account.auxiliary.invoices.wizard'

    def preview_html(self):
        self.ensure_one()
        action_report = self.env["ir.actions.report"].search(
            [
                ("report_name", "=",
                 'account_report_agromark.account_auxiliary_invoices_template'),
                ("report_type", "=", 'qweb-html')
            ],
            limit=1,
        )
        if not action_report:
            raise ValidationError(_(
                'Not found report ID: account_report_agromark.account_auxiliary_invoices_template'
            ))
        data_report = {}
        out = action_report.report_action(self, data=data_report)
        return out
    
    
    def data_report_preview(self):
        self.ensure_one()
        header = self.prepare_header()
        data = self.prepare_data()
        report_name = self.report_type == 'local' and \
            _('Auxiliar de Impuestos') or \
            _('Auxiliar de Impuestos NIIF')
        company = self.env.company.name
        vat = self.env.company.vat
        date_from = self.date_from
        date_to = self.date_to

        html_text = '''
            <div class="report_aux">
                table_header
            </div>
            <div class="act_as_table list_table" style="margin-top: 10px;"/>
            <div class="report_aux">
                <div class="act_as_table data_table">
                    <div class="act_as_thead">
                        <div class="act_as_row labels">
                            th_report
                        </div>
                    </div>
                    data_report
                </div>
            </div>
        '''

        # THEAD
        th_text = ''
        for th in header:
            th_text += '<div class="act_as_cell">%s</div>' % th[1]

        html_text = html_text.replace('th_report', th_text)

        # TBODY
        tr_text = ''
        c = 1
        for tr_data in data.get('report_data', []):
            tr_text += '<div class="act_as_row lines">'
            bold = False
            for k, v in tr_data.items():
                if k == 'bold':
                    bold = v
                elif k in ('group', 'account_id', 'parent_id', 'group_id'):
                    continue
                else:
                    class_span = ' '.join([
                        bold and
                        'bold-cell-report back-cell' or
                        'normal-cell-report',
                        k in ('initial', 'debit', 'credit', 'final',
                              'balance', 'residual') and 'amount' or 'left'
                    ])
                    tr_text += '<div class="act_as_cell %s">%s</div>' % (
                        class_span,
                        type(v) in (type(2), type(2.3)
                                    ) and '{:.2f}'.format(v) or v or ''
                    )
            tr_text += '</div>'
            c += 1

        html_text = html_text.replace('data_report', tr_text)
        now = fields.Datetime.context_timestamp(
            self,
            fields.Datetime.now()
        ).strftime('%d-%m-%Y %H:%M:%S')

        # HEADER
        table_h = '''
            <div class="act_as_table data_table">
                <div class="act_as_row">
                    <div class="act_as_cell labels">{inf_tag}</div>
                    <div class="act_as_cell">{inf_val}</div>
                    <div class="act_as_cell labels">{dat_tag}</div>
                    <div class="act_as_cell">{dat_val}</div>
                </div>
                <div class="act_as_row">
                    <div class="act_as_cell labels">{com_tag}</div>
                    <div class="act_as_cell">{com_val}</div>
                    <div class="act_as_cell labels">{ini_tag}</div>
                    <div class="act_as_cell">{ini_val}</div>
                </div>
                <div class="act_as_row">
                    <div class="act_as_cell labels">{nit_tag}</div>
                    <div class="act_as_cell">{nit_val}</div>
                    <div class="act_as_cell labels">{end_tag}</div>
                    <div class="act_as_cell">{end_val}</div>
                </div>
                <div class="act_as_row">
                    <div class="act_as_cell labels">{type_tag}</div>
                    <div class="act_as_cell">{type_val}</div>
                    <div class="act_as_cell labels"></div>
                    <div class="act_as_cell"></div>
                </div>
            </div>
        '''.format(
            inf_tag=_('Report'),
            inf_val=report_name,
            dat_tag=_('Date'),
            dat_val=now,
            com_tag=_('Company'),
            com_val=company,
            ini_tag=_('From'),
            ini_val=date_from,
            nit_tag=_('NIT'),
            nit_val=vat,
            end_tag=_('To'),
            end_val=date_to,
            type_tag=_('Type'),
            type_val=REPORT_TYPE.get(self.report_type)
        )

        html_text = html_text.replace('table_header', table_h)
        return html_text