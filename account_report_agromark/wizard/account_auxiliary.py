# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError


class AccountauxiliaryWizard(models.Model):
    _inherit = 'account.auxiliary.wizard'

    account_analityc_ids = fields.Many2many(comodel_name='account.analytic.account',
                                    string='Analytic accounts')
    account_analityc = fields.Boolean('Cuenta analítica?', default=False)

    @api.onchange('partner_by')
    def onchange_partner_by(self):
        if self.partner_by:
            self.account_by = False
            self.group_by = False
        else:
            pass
    
    @api.onchange('account_by')
    def onchange_account_by(self):
        if self.account_by:
            self.group_by = False
            self.partner_by = False
        else:
            pass
    
    @api.onchange('group_by')
    def onchange_group_by(self):
        if self.group_by:
            self.account_by = False
            self.partner_by = False
        else:
            pass

    @api.onchange('account_by', 'group_by')
    def onchange_account_group_by(self):
        if self.account_by or self.group_by:
            pass
        else:
            pass

    def prepare_data2(self):
        query_data_detail = self.prepare_data_detail()
        query_data_acc_rp = self.prepare_data_acc_rp()
        query_data_acc = self.prepare_data_acc()
        query_data_rp = self.prepare_data_rp()

        data_detail = self._execute_query(query_data_detail)
        query_data = data_detail
        if self.group_by:
            data_acc_rp = self._execute_query(query_data_acc_rp)
            data_acc = self._execute_query(query_data_acc)
            query_data += data_acc_rp
            query_data += data_acc
            query_data = sorted(
                query_data,
                key=lambda r: [r['code'], r['partner'], r['date'], r['move'], not r['bold']]
            )
        if self.account_by:
            data_acc = self._execute_query(query_data_acc)
            query_data += data_acc
            query_data = sorted(
                query_data,
                key=lambda r: [r['code'], r['date'], r['move'], not r['bold']]
            )
        if self.partner_by:
            data_rp = self._execute_query(query_data_rp)
            query_data += data_rp
            query_data = sorted(
                query_data,
                key=lambda r: [r['partner'], r['code'], r['date'], r['move'], not r['bold']]
            )
        return {'report_data': query_data and query_data or []}

    def _get_query_where(self):
        where = super(AccountauxiliaryWizard, self)._get_query_where()
        if self.account_analityc_ids:
            account_analityc_ids = self.account_analityc_ids.ids
            aaids = str(tuple(account_analityc_ids)).replace(',)', ')')
            where += """
            and aml.analytic_account_id in %s
            """ % aaids
        return where

    def prepare_data_detail(self):
        query = super(AccountauxiliaryWizard, self).prepare_data_detail()
        if self.account_analityc:
            query = query.replace('aj.name as journal,',
                                  '''aj.name as journal,
                                  aal.name as analytic,''')
        query = query.replace("'' as final",
                            ''''' as final,
                            CASE 
                                WHEN am.state = 'draft' THEN 'Borrador'
                                WHEN am.state = 'posted' THEN 'Publicado'
                                WHEN am.state = 'cancel' THEN 'Cancelado'
                            ELSE 'N/A' END as state''')
        if self.account_analityc:
            query = query.replace('left join res_partner rp on rp.id = aml.partner_id',
                '''left join res_partner rp on rp.id = aml.partner_id
                    left join account_analytic_account aal on aal.id = aml.analytic_account_id''')
        return query
    
    def prepare_header(self):
        header = super(AccountauxiliaryWizard, self).prepare_header()
        if self.account_analityc:
            header.insert(6, ('analytic', _('Account Analytic')))

        header.append(('state', _('Estado')))
        return header

    def prepare_data_acc_rp(self):
        query = super(AccountauxiliaryWizard, self).prepare_data_acc_rp()
        query = query.replace("'' as date,",
            "DATE('%s') as date," % self.date_from)
        if self.account_analityc:
            query = query.replace("'' as journal,", 
                "'' as journal,\n '' as analytic,")
        query = query.replace("as final",
            "as final, '' as state")
        return query

    def prepare_data_rp(self):
        query = super(AccountauxiliaryWizard, self).prepare_data_rp()
        query = query.replace("'' as date,",
            "DATE('%s') as date," % self.date_from)
        if self.account_analityc:
            query = query.replace(
            "'' as journal,",
            "'' as journal,\n '' as analytic,"
            )
        query = query.replace("as final",
            "as final, '' as state")
        return query

    def prepare_data_acc(self):
        query = super(AccountauxiliaryWizard, self).prepare_data_acc()
        query = query.replace("'' as date,",
            "DATE('%s') as date," % self.date_from)
        if self.account_analityc:
            query = query.replace("'' as journal,", 
                          "'' as journal,\n '' as analytic,")
        query = query.replace("as final",
            "as final, '' as state")
        return query

