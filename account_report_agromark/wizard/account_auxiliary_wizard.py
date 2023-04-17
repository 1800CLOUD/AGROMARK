# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountauxiliaryWizard(models.Model):
    _inherit = 'account.auxiliary.wizard'

    account_analityc_ids = fields.Many2many(comodel_name='account.analytic.account',
                                    string='Accounts')

    
    def _get_query_where(self):
        ids_companies = self.env.companies.ids
        ids_companies = str(tuple(ids_companies)).replace(',)', ')')
        where = 'and aml.company_id in %s' % ids_companies

        if self.line_state:
            where += """
                and aml.parent_state = 'posted'
            """
        if self.report_type == 'ifrs':
            where += """
                and aml.ifrs_type != 'local'
            """
        else:
            where += """
                and aml.ifrs_type != 'ifrs'
            """
        if self.accounts_ids:
            accounts_ids = self.accounts_ids.ids
            aids = str(tuple(accounts_ids)).replace(',)', ')')
            where += """
            and aml.account_id in %s
            """ % aids
        if self.partners_ids:
            partners_ids = self.partners_ids.ids
            pids = str(tuple(partners_ids)).replace(',)', ')')
            where += """
            and aml.partner_id in %s
            """ % pids
        if self.account_analityc_ids:
            account_analityc_ids = self.account_analityc_ids.ids
            aaids = str(tuple(account_analityc_ids)).replace(',)', ')')
            where += """
            and aml.analytic_account_id in %s
            """ % aaids
            
        if self.no_zero:
            where += """
            and coalesce(aml.{debit}, 0) - coalesce(aml.{credit}, 0) != 0
            """.format(
                debit= self.report_type == 'ifrs' and 'ifrs_debit' or 'debit',
                credit= self.report_type == 'ifrs' and 'ifrs_credit' or 'credit')
        return where
    
    def prepare_data_detail(self):
        query = """
        select
            False as bold,
            False as group,
            aa.id as account_id,
            aa.code as code,
            aa.name as name,
            rp.vat as vat,
            coalesce(rp.name, '**') as partner,
            aml.date as date,
            aj.name as journal,
            aal.name as analytic,
            am.name as move,
            aml.name as line,
        """

        if self.currency_by:
            query += """
                rc.name as currency,
                aml.amount_currency as amount,
            """

        query += """
            '' as initial,
            coalesce(aml.{debit}, 0) as debit,
            coalesce(aml.{credit}, 0) as credit,
            '' as final,
            CASE 
                WHEN am.state = 'draft' THEN 'Borrador'
                WHEN am.state = 'posted' THEN 'Publicado'
                WHEN am.state = 'cancel' THEN 'Cancelado'
            ELSE 'N/A' END
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        inner join account_journal aj on aj.id = aml.journal_id
        left join account_analytic_account aal on aal.id = aml.analytic_account_id
        left join res_partner rp on rp.id = aml.partner_id
        """.format(
            credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
            debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
            date_start=self.date_from,
            date_end=self.date_to
        )

        if self.currency_by:
            query += """
            left join res_currency rc on rc.id = aml.currency_id
            """

        query += """
        where aml.date between '%s' and '%s'
        %s
        """ % (
            self.date_from,
            self.date_to,
            self._get_query_where()
        )

        query += """
        order by aa.code, rp.name, aml.date
        """
        return query
    
    def prepare_header(self):
        report_header = [
            ('code', _('Code')),
            ('name', _('Name')),
            ('vat', 'NIT'),
            ('partner', _('Partner')),
            ('date', _('Date')),
            ('journal', _('Journal')),
            ('analytic', _('Account Analytic')),
            ('move', _('Move')),
            ('line', _('Line')),
        ]

        if self.currency_by:
            report_header += [
                ('currency', _('Currency')),
                ('amount', _('Amount')),
            ]

        report_header += [
            ('initial', _('Initial')),
            ('debit', _('Debit')),
            ('credit', _('Credit')),
            ('final', _('Final')),
            ('state', _('Estado')),
        ]

        return report_header

    def prepare_data_acc_rp(self):
        res = super(AccountauxiliaryWizard, self).prepare_data_acc_rp()
        res = res.replace("'' as journal,", 
                          "'' as journal,\n '' as analytic,")
        return res

    def prepare_data_acc(self):
        res = super(AccountauxiliaryWizard, self).prepare_data_acc()
        res = res.replace("'' as journal,", 
                          "'' as journal,\n '' as analytic,")
        return res