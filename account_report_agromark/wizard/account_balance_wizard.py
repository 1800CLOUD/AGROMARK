# -*- coding: utf-8 -*-

import logging
from tokenize import group

from odoo import _, fields, models
from odoo.exceptions import ValidationError

REPORT_TYPE = {
    'local': 'Local',
    'ifrs': 'NIIF'
}

#class AccountaBalanceWizard(models.Model):
#    _inherit = 'account.balance.wizard'
#
#    account_analityc_ids = fields.Many2many(comodel_name='account.analytic.account',
#                                    string='Accounts')
#
#
#
#    def update_amounts_line(self, sum_line):
#        sum_line = {
#            'bold': sum_line['bold'],
#            'group': sum_line['group'],
#            'account_id': sum_line['account_id'],
#            'parent_id': '',
#            'group_id': '',
#            'code': sum_line['code'],
#            'name': sum_line['name'],
#            'analytic_name': '',
#            'vat': '',
#            'partner': '',
#            'residual': sum_line['residual'],
#            'debit': sum_line['debit'],
#            'credit': sum_line['credit'],
#            'balance': sum_line['balance'],
#        }
#        return sum_line
#
#    def prepare_data(self):
#        query_data = self.prepare_data_query()
#        sum_line = query_data.pop()
#        copy_data = list(query_data)
#
#        if self.group_by:
#            aids = [rd.get('account_id') for rd in copy_data]
#            aids = list(set(aids))
#            accounts = self.env['account.account'].browse(aids)
#            for account in accounts:
#                datas = [
#                    rd for rd in copy_data if rd.get(
#                        'account_id') == account.id
#                ]
#                values = {
#                    'bold': True,
#                    'group': False,
#                    'account_id': account.id,
#                    'parent_id': False,
#                    'group_id': '',
#                    'code': account.code,
#                    'name': account.name,
#                }
#                if self.partner_by:
#                    values.update({
#                        'vat': '',
#                        'partner': '',
#                    })
#                values.update({
#                    'analytic_name': '/',
#                    'residual': sum(d.get('residual') for d in datas),
#                    'debit': sum(d.get('debit') for d in datas),
#                    'credit': sum(d.get('credit') for d in datas),
#                    'balance': sum(d.get('balance') for d in datas),
#                })
#                    
#                query_data.append(values)
#
#        copy_data = list(query_data)
#        parents = False
#        if self.group_by:
#            aids = [cp.get('account_id') for cp in copy_data]
#            aids = list(set(aids))
#            accounts = self.env['account.account'].browse(aids)
#            groups = self.env['account.group'].search([])
#            parents = groups
#            code_groups = []
#            while parents:
#                for parent in parents:
#                    if parent.id not in code_groups:
#                        aids = parent.compute_account_ids.ids
#                        datas = [
#                            cp for cp in copy_data if cp.get('bold') and
#                            cp.get('account_id') in aids
#                        ]
#                        values = {
#                            'bold': True,
#                            'group': True,
#                            'account_id': False,
#                            'parent_id': parent.parent_id and
#                            parent.parent_id.id or
#                            False,
#                            'group_id': parent.id,
#                            'code': parent.code,
#                            'name': parent.name,
#                        }
#
#                        if self.partner_by:
#                            values.update({
#                                'vat': '',
#                                'partner': '',
#                            })
#                        values.update({
#                            'residual': sum(d.get('residual') for d in datas),
#                            'debit': sum(d.get('debit') for d in datas),
#                            'credit': sum(d.get('credit') for d in datas),
#                            'balance': sum(d.get('balance') for d in datas),
#                        })
#
#                        if self.no_zero and \
#                            (values['residual'] != 0 or
#                             values['balance'] != 0):
#                            # and values['debit'] - values['credit'] != 0:
#                            query_data.append(values)
#                        elif not self.no_zero:
#                            query_data.append(values)
#                    code_groups.append(parent.id)
#                parents = parents.parent_id
#
#            if self.group_by and groups:
#                query_data = sorted(
#                    query_data,
#                    key=lambda r: [r.get('code'), not r.get('bold')]
#                )
#
#        if self.partner_by or parents:
#            sum_line = self.update_amounts_line(sum_line)
#
#        query_data.append(sum_line)
#        return {'report_data': query_data and query_data or []}
#
#
#    def sum_amounts(self, data_query):
#        accounts_list = []
#        for line in data_query:
#            if line['account_id'] not in accounts_list:
#                accounts_list.append(line['account_id'])
#        residual = sum(i['residual'] for i in data_query)
#        debit = sum(i['debit'] for i in data_query)
#        credit = sum(i['credit'] for i in data_query)
#        balance = sum(i['balance'] for i in data_query)
#        #analytic_name = [i.get('analytic_name') for i in data_query]
#        sum_line = {
#            'bold': True,
#            'group': False,
#            'account_id': '',
#            'parent_id': '',
#            'group_id': '',
#            'code': '',
#            'name': 'Total',
#            'analytic_name': '',
#            'residual': residual,
#            'debit': debit,
#            'credit': credit,
#            'balance': balance
#        }
#        data_query.append(sum_line)
#        return data_query
#
#    def prepare_query(self):
#        query_account = self.prepare_query_account()
#        query_before = self.prepare_query_before()
#        query_after = self.prepare_query_after()
#
#        query = """
#        select 
#            False as bold,
#            False as group,
#            aml.account_id,
#            '' as parent_id,
#            '' as group_id,
#            aml.code,
#            aml.name,
#            aml.analytic_name,
#        """
#
#        if self.partner_by:
#            query += """
#                aml.vat,
#                aml.partner,
#            """
#
#        query += """
#        coalesce(amlb.debit, 0) - coalesce(amlb.credit, 0) as residual,
#        coalesce(amla.debit, 0) as debit,
#        coalesce(amla.credit, 0) as credit,
#        (coalesce(amlb.debit, 0) - coalesce(amlb.credit, 0)) +
#         (coalesce(amla.debit, 0) - coalesce(amla.credit, 0)) as balance
#        from (%s) aml
#        left join (%s) amlb on
#        """ % (query_account, query_before)
#
#        if self.partner_by:
#            query += """
#             (
#                (amlb.account_id = aml.account_id AND
#                 amlb.partner_id = aml.partner_id)
#                OR
#                (amlb.account_id = aml.account_id AND
#                 amlb.partner_id is null AND aml.partner_id is null)
#            )
#            """
#        else:
#            query += """
#             amlb.account_id = aml.account_id 
#            """
#
#        query += """
#        left join (%s) amla on
#        """ % (query_after)
#
#        if self.partner_by:
#            query += """
#             (
#                (amla.account_id = aml.account_id AND
#                 amla.partner_id = aml.partner_id)
#                OR
#                (amla.account_id = aml.account_id AND
#                 amla.partner_id is null AND aml.partner_id is null)
#            )
#            """
#        else:
#            query += """
#             amla.account_id = aml.account_id 
#            """
#        if self.no_zero:
#            query += """
#            where coalesce(amlb.debit, 0) - coalesce(amlb.credit, 0) != 0
#                or (
#                    coalesce(amlb.debit, 0) - coalesce(amlb.credit, 0)
#                ) + (
#                    coalesce(amla.debit, 0) - coalesce(amla.credit, 0)
#                ) != 0
#            """
#
#        return query
#
#    def prepare_query_account(self):
#        date = self.date_to.strftime('%Y-%m-%d')
#        ids_companies = self.env.companies.ids
#        ids_companies = str(tuple(ids_companies)).replace(',)', ')')
#
#        query = """
#        select aa.id as account_id, aa.code, aa.name, aal.name as analytic_name
#        """
#
#        if self.partner_by:
#            query += """
#            , aml.partner_id, rp.vat, rp.name as partner
#            """
#
#        query += """
#        from account_move_line aml
#        """
#
#        query += """
#            inner join account_account aa on aa.id = aml.account_id
#            """
#        
#        query += """
#            left join account_analytic_account aal on aal.id = aml.analytic_account_id
#            """
#
#        if self.partner_by:
#            query += """
#            left join res_partner rp on rp.id = aml.partner_id
#            """
#
#        query += """
#        where aml.date <= '%s'
#        and aml.company_id in %s
#        """ % (date, ids_companies)
#
#        if self.line_state:
#            query += """
#            and aml.parent_state = 'posted'
#            """
#
#        if self.accounts_ids:
#            accounts_ids = self.accounts_ids.ids
#            aids = str(tuple(accounts_ids)).replace(',)', ')')
#            query += """
#            and aml.account_id in %s
#            """ % aids
#        
#        if self.account_analityc_ids:
#            account_analityc_ids = self.account_analityc_ids.ids
#            aaids = str(tuple(account_analityc_ids)).replace(',)', ')')
#            query += """
#            and aml.analytic_account_id in %s
#            """ % aaids
#
#        if self.partner_by and self.partners_ids:
#            partners_ids = self.partners_ids.ids
#            pids = str(tuple(partners_ids)).replace(',)', ')')
#            query += """
#            and aml.partner_id in %s
#            """ % pids
#
#        query += """
#        group by aa.id, aa.code, aa.name
#        """
#
#        if self.partner_by:
#            query += """
#            , aml.partner_id, rp.vat, rp.name
#            """
#        query += """
#        , analytic_name
#        """
#        query += """
#        order by aa.code
#        """
#
#        return query
#
#    def prepare_query_before(self):
#        date = self.date_from.strftime('%Y-%m-%d')
#        ids_companies = self.env.companies.ids
#        ids_companies = str(tuple(ids_companies)).replace(',)', ')')
#
#        query = """
#        select aa.id as account_id, aal.name as analytic_name,
#        """
#
#        if self.partner_by:
#            query += """
#            aml.partner_id,
#            """
#
#        if self.report_type == 'ifrs':
#            query += """
#            sum(aml.ifrs_debit) as debit,
#            sum(aml.ifrs_credit) as credit
#            """
#        else:
#            query += """
#            sum(aml.debit) as debit,
#            sum(aml.credit) as credit
#            """
#
#        query += """
#        from account_move_line aml
#        """
#
#        query += """
#            inner join account_account aa on aa.id = aml.account_id
#            """
#        
#        query += """
#            left join account_analytic_account aal on aal.id = aml.analytic_account_id
#            """
#
#        query += """
#        where aml.date < '%s'
#        """ % date
#        query += """
#        and aml.company_id in %s
#        """ % ids_companies
#
#        if self.line_state:
#            query += """
#            and aml.parent_state = 'posted'
#            """
#        if self.report_type == 'ifrs':
#            query += "and aml.ifrs_type != 'local'"
#        else:
#            query += "and aml.ifrs_type != 'ifrs'"
#
#        if self.partner_by and self.partners_ids:
#            partners_ids = self.partners_ids.ids
#            pids = str(tuple(partners_ids)).replace(',)', ')')
#            query += """
#            and aml.partner_id in %s
#            """ % pids
#
#        query += """
#        group by aa.id
#        """
#
#        if self.partner_by:
#            query += """
#            , aml.partner_id
#            """
#
#        query += """
#        , analytic_name
#        """
#        
#        return query
#
#    def prepare_query_after(self):
#        date_from = self.date_from.strftime('%Y-%m-%d')
#        date_to = self.date_to.strftime('%Y-%m-%d')
#        ids_companies = self.env.companies.ids
#        ids_companies = str(tuple(ids_companies)).replace(',)', ')')
#
#        query = """
#        select aa.id as account_id, aal.name as analytic_name,
#        """
#
#        if self.partner_by:
#            query += """
#            aml.partner_id,
#            """
#
#        if self.report_type == 'ifrs':
#            query += """
#            sum(aml.ifrs_debit) as debit,
#            sum(aml.ifrs_credit) as credit
#            """
#        else:
#            query += """
#            sum(aml.debit) as debit,
#            sum(aml.credit) as credit
#            """
#
#        query += """
#        from account_move_line aml
#        """
#
#        query += """
#            inner join account_account aa on aa.id = aml.account_id
#            """
#        query += """
#            left join account_analytic_account aal on aal.id = aml.analytic_account_id
#            """
#        query += """
#        where aml.date between '%s' and '%s'
#        """ % (date_from, date_to)
#        query += """
#        and aml.company_id in %s
#        """ % ids_companies
#
#        if self.line_state:
#            query += """
#            and aml.parent_state = 'posted'
#            """
#
#        if self.report_type == 'ifrs':
#            query += "and aml.ifrs_type != 'local'"
#        else:
#            query += "and aml.ifrs_type != 'ifrs'"
#
#        query += """
#        group by aa.id
#        """
#
#        if self.partner_by:
#            query += """
#            , aml.partner_id
#            """
#        query += """
#        , analytic_name
#        """
#        return query
#
#    def prepare_header(self):
#        report_header = [
#            ('code', _('Code')),
#            ('name', _('Name')),
#            ('analytic_name', _('Analytic Account Name')),
#        ]
#
#        if self.partner_by:
#            report_header += [
#                ('vat', 'NIT'),
#                ('partner', _('Partner'))
#            ]
#
#        report_header += [
#            ('residual', _('Residual amount (balance)')),
#            ('debit', _('Debit')),
#            ('credit', _('Credit')),
#            ('balance', _('Balance amount'))
#        ]
#
#        return report_header