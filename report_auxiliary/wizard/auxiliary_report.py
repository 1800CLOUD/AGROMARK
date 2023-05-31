# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError

REPORT_TYPE = {
    'local': 'Local',
    'ifrs': 'NIIF'
}

_logger = logging.getLogger(__name__)


class AccountauxiliaryWizard(models.Model):
    _name = 'report.auxiliary.wizard'
    _description = 'Reporte Auxiliar'

    accounts_ids = fields.Many2many(comodel_name='account.account',
                                    string='Cuentas')
    currency_by = fields.Boolean('Multimoneda?',
                                 default=False,)
    date_from = fields.Date('Desde',
                            default=fields.Date.today())
    date_to = fields.Date('Hasta',
                          default=fields.Date.today())
    group_by = fields.Boolean('Por cuenta y Tercero',
                              default=False,
                              help='Totalizado por cuenta')
    line_state = fields.Boolean('Publicado?',
                                default=True)
    partner_by = fields.Boolean('Por Tercero',
                                help='Totalizado por tercero')
    account_by = fields.Boolean('Por Cuenta',
                                help='Totals per partner')
    partners_ids = fields.Many2many(comodel_name='res.partner',
                                    string='Terceros')
    report_type = fields.Selection(selection=[('local', 'Local'),
                                              ('ifrs', 'NIIF')],
                                   default='local',
                                   required="True")
    group_by_partner = fields.Boolean('Group by partner',
                                      default=False,)
    no_zero = fields.Boolean('Omitir saldos en cero',
                             default=True)
    account_analityc_ids = fields.Many2many(comodel_name='account.analytic.account',
                                    string='Cuentas Analiticas')
    account_analityc = fields.Boolean('Cuenta analítica?', default=False)
    
    @api.onchange('partner_by', 'account_by', 'group_by')
    def onchange_partner_by(self):
        if self.partner_by:
            self.account_by = False
            self.group_by = False
        else:
            pass
    
    @api.onchange('account_by', 'group_by')
    def onchange_account_group_by(self):
        if self.account_by or self.group_by:
            self.partner_by = False
        else:
            pass


    def action_confirm(self):
        report = self.env.ref('report_auxiliary.report_auxiliary_agr')
        data = self.prepare_data2()
        return report.report_action(self, data=data)

    def compute_initial_amount_by_partner(self, partner_id, account):
        domain = [
            ('partner_id', '=', partner_id),
            ('date', '<', self.date_from),
        ]
        if self.line_state:
            domain.append(('parent_state', '=', 'posted'))

        if self.report_type == 'local':
            domain.append(('account_id', '=', account.id))
        else:
            domain.append(('account_id.ifrs_account_id', '=', account.id))

        lines = self.env['account.move.line'].search(domain)
        if self.report_type == 'local':
            initial = sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
        else:
            initial = sum(
                lines.mapped('ifrs_debit')
            ) - sum(
                lines.mapped('ifrs_credit')
            )
        return initial

    def group_total_amounts_for_partners(self, query_data, account):
        partner_lines = []
        partner_ids = [
            (rd.get('vat'), rd.get('partner'))
            for rd in query_data if rd.get('account_id') == account.id
        ]
        partner_ids = list(set(partner_ids))
        for partner_id in partner_ids:
            filter_lines = [
                rd for rd in query_data if rd.get('vat') == partner_id[0] and
                rd.get('account_id') == account.id
            ]
            initial_amount = self.compute_initial_amount_by_partner(
                partner_id[0], account)
            debit = sum(d.get('debit') for d in filter_lines)
            credit = sum(d.get('credit') for d in filter_lines)
            final = initial_amount + (debit - credit)
            values = {
                'bold': True,
                'group': False,
                'account_id': account.id,
                'code': account.code,
                'name': '',
                'vat': partner_id[0],
                'partner': partner_id[1],
                'date': '',
                'journal': '',
                'move': '',
                'line': 'Total: ' + partner_id[1],
            }
            if self.currency_by:
                values.update({
                    'currency': '',
                    'amount': '',
                })

            values.update({
                'initial': initial_amount,
                'debit': debit,
                'credit': credit,
                'final': final,
            })
            partner_lines.append(values)
        return partner_lines

    def prepare_data2(self):
        query_data_detail = self.prepare_data_detail()
        query_data_acc_rp = self.prepare_data_acc_rp()
        query_data_acc = self.prepare_data_acc()
        query_data_rp = self.prepare_data_rp()

        data_detail = self._execute_query(query_data_detail)
        query_data = data_detail
        if self.group_by:
            data_acc_rp = self._execute_query(query_data_acc_rp)
            query_data += data_acc_rp
            query_data = sorted(
                query_data,
                key=lambda r: [r['code'], r['partner'], not r['bold']]
            )
        if self.account_by:
            data_acc = self._execute_query(query_data_acc)
            query_data += data_acc
            query_data = sorted(
                query_data,
                key=lambda r: [r['code'], not r['bold']]
            )
        if self.partner_by:
            data_rp = self._execute_query(query_data_rp)
            query_data += data_rp
            query_data = sorted(
                query_data,
                key=lambda r: [r['partner'], not r['bold']]
            )
        else:
            query_data = sorted(
                query_data,
                key=lambda r: [r['date'], r['move'], r['partner'], not r['bold']]
            )

        return {'report_data': query_data and query_data or []}

    def _execute_query(self, query):
        self.env.cr.execute(query)
        data_query = self.env.cr.dictfetchall()
        return data_query

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
    

    def _get_query_where2(self):
        where = self._get_query_where()
        where = where.replace('aml', 'aml2')
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
        """
        if self.account_analityc:
            query += """
                aal.name as analytic,
                """
           
        query += """
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
            ELSE 'N/A' END as state
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        inner join account_journal aj on aj.id = aml.journal_id
        left join res_partner rp on rp.id = aml.partner_id
        """.format(
            credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
            debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
            date_start=self.date_from,
            date_end=self.date_to
        )

        if self.account_analityc:
            query += """
                left join account_analytic_account aal on aal.id = aml.analytic_account_id
                """
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
        order by aml.date, am.name, rp.name
        """
        if self.partner_by and 1 == 0:
            query = query.replace(
                "'' as initial",
                '''coalesce((
                    select sum(aml2.{debit} - aml2.{credit})
                    from account_move_line as aml2
                    inner join account_move am2 on am2.id = aml2.move_id
                    where aml2.account_id = aa.id
                    and (
                        aml2.partner_id = aml.partner_id
                        or
                        (
                            aml2.partner_id is null
                            and
                            aml.partner_id is null
                        )
                    )
                    and aml2.date < '{date_start}'
                    {where2}
                ), 0) as initial
                '''
            ).replace(
                "'' as final",
                '''coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where aml2.account_id = aa.id
                and (
                    aml2.partner_id = aml.partner_id
                    or
                    (
                        aml2.partner_id is null
                        and
                        aml.partner_id is null
                    )
                )
                and aml2.date <= '{date_end}'
                {where2}
            ), 0) as final
                '''
            ).format(
                credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
                debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
                date_start=self.date_from,
                date_end=self.date_to,
                where=self._get_query_where(),
                where2=self._get_query_where2()
            )
        return query
    
    def prepare_data_acc_rp(self):
        query = """
        select
            True as bold,
            False as group,
            aa.id as account_id,
            aa.code as code,
            aa.name as name,
            rp.vat as vat,
            coalesce(rp.name, '**') as partner,
            '' as date,
            '' as journal,
        """

        if self.account_analityc :
            query += """
                '' as analytic, 
            """

        query += """
            '' as move,
            '' as line,
        """

        if self.currency_by:
            query += """
                '' as currency,
                '' as amount,
            """

        query += """
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where aml2.account_id = aa.id
                and (
                    aml2.partner_id = aml.partner_id
                    or
                    (
                        aml2.partner_id is null
                        and
                        aml.partner_id is null
                    )
                )
                and aml2.date < '{date_start}'
                {where2}
            ), 0) as initial,
            sum(coalesce(aml.{debit}, 0)) as debit,
            sum(coalesce(aml.{credit}, 0)) as credit,
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where aml2.account_id = aa.id
                and (
                    aml2.partner_id = aml.partner_id
                    or
                    (
                        aml2.partner_id is null
                        and
                        aml.partner_id is null
                    )
                )
                and aml2.date <= '{date_end}'
                {where2}
            ), 0) as final
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        left join res_partner rp on rp.id = aml.partner_id
        where aml.date between '{date_start}' and '{date_end}'
        {where}
        """.format(
            credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
            debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
            date_start=self.date_from,
            date_end=self.date_to,
            where=self._get_query_where(),
            where2=self._get_query_where2()
        )

        # if self.accounts_ids:
        #     accounts_ids=self.accounts_ids.ids
        #     aids=str(tuple(accounts_ids)).replace(',)', ')')
        #     query += """
        #     and aml.account_id in %s
        #     """ % aids

        # if self.partners_ids:
        #     partners_ids=self.partners_ids.ids
        #     pids=str(tuple(partners_ids)).replace(',)', ')')
        #     query += """
        #     and aml.partner_id in %s
        #     """ % pids

        query += """
        group by aml.partner_id, rp.name, rp.vat, aa.code, aa.id
        order by rp.name
        """
        return query
    
    def prepare_data_rp(self):
        query = """
        select
            True as bold,
            False as group,
            -- aa.id as account_id,
            -- aa.code as code,
            -- aa.name as name,
            '' as account_id,
            '' as code,
            '' as name,
            rp.vat as vat,
            coalesce(rp.name, '**') as partner,
            '' as date,
            '' as journal,
        """
        if self.account_analityc :
            query += """
                '' as analytic, 
            """

        query += """
            '' as move,
            '' as line,
            '' as state,
        """

        if self.currency_by:
            query += """
                '' as currency,
                '' as amount,
            """

        query += """
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where (aml2.partner_id = aml.partner_id 
                        OR
                        (aml2.partner_id is null AND aml.partner_id is null))
                    AND aml2.date < '{date_start}'
                    {where2}
            ), 0) as initial,
            sum(coalesce(aml.{debit}, 0)) as debit,
            sum(coalesce(aml.{credit}, 0)) as credit,
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where (aml2.partner_id = aml.partner_id
                        OR
                        (aml2.partner_id is null AND aml.partner_id is null))
                    AND aml2.date <= '{date_end}'
                    {where2}
                ), 0) as final
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        left join res_partner rp on rp.id = aml.partner_id
        where aml.date between '{date_start}' and '{date_end}'
            {where}
        """.format(
            credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
            debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
            date_start=self.date_from,
            date_end=self.date_to,
            where=self._get_query_where(),
            where2=self._get_query_where2()
        )

        query += """
        group by aa.id, rp.vat, rp.name
        order by rp.vat
        """
        return query

    def prepare_data_acc(self):
        query = """
        select
            True as bold,
            False as group,
            aa.id as account_id,
            aa.code as code,
            aa.name as name,
            '' as vat,
            '' as partner,
            '' as date,
            '' as journal,
        """

        if self.account_analityc :
            query += """
                '' as analytic, 
            """

        query += """
            '' as move,
            '' as line,
        """

        if self.currency_by:
            query += """
                '' as currency,
                '' as amount,
            """

        query += """
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where aml2.account_id = aa.id
                and aml2.date < '{date_start}'
                {where2}
            ), 0) as initial,
            sum(coalesce(aml.{debit}, 0)) as debit,
            sum(coalesce(aml.{credit}, 0)) as credit,
            coalesce((
                select sum(aml2.{debit} - aml2.{credit})
                from account_move_line as aml2
                inner join account_move am2 on am2.id = aml2.move_id
                where aml2.account_id = aa.id
                and aml2.date <= '{date_end}'
                {where2}
            ), 0) as final
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        where aml.date between '{date_start}' and '{date_end}'
        {where}
        """.format(
            credit=self.report_type == 'local' and 'credit' or 'ifrs_credit',
            debit=self.report_type == 'local' and 'debit' or 'ifrs_debit',
            date_start=self.date_from,
            date_end=self.date_to,
            where=self._get_query_where(),
            where2=self._get_query_where2()
        )

        # if self.accounts_ids:
        #     accounts_ids=self.accounts_ids.ids
        #     aids=str(tuple(accounts_ids)).replace(',)', ')')
        #     query += """
        #     and aml.account_id in %s
        #     """ % aids

        # if self.partners_ids:
        #     partners_ids=self.partners_ids.ids
        #     pids=str(tuple(partners_ids)).replace(',)', ')')
        #     query += """
        #     and aml.partner_id in %s
        #     """ % pids

        query += """
        group by aa.code, aa.id
        order by aa.code
        """
        return query

    # def prepare_data(self):
    #     Line = self.env['account.move.line']

    #     query_data = self.prepare_data_query()
    #     copy_data = list(query_data)

    #     aids = [rd.get('account_id') for rd in copy_data]
    #     aids = list(set(aids))
    #     pids = [rd.get('partner_id') for rd in copy_data]
    #     pids = list(set(pids))
    #     accounts = self.env['account.account'].browse(aids)
    #     partners = self.env['res.partner'].browse(pids)
    #     for account in accounts:
    #         datas_by_account = list(filter(
    #             lambda x: x.get('account_id') == account.id,
    #             copy_data
    #         ))
    #         # lines without partner
    #         data_by_acc_no_partner = list(filter(
    #             lambda x: x.get('account_id') == account.id and \
    #                 not x.get('partner_id'),
    #             copy_data
    #         ))
    #         acc_initial = sum(
    #               x.get('initial') for x in data_by_acc_no_partner)
    #         acc_final = sum(x.get('final') for x in data_by_acc_no_partner)
    #         acc_debit = sum(x.get('debit') for x in data_by_acc_no_partner)
    #         acc_credit = sum(x.get('credit') for x in data_by_acc_no_partner)
    #         # lines with partner
    #         acc_pids = list(set(map(
    #             lambda x: x.get('partner_id'),
    #             datas_by_account
    #         )))
    #         for pid in acc_pids:
    #             datas_by_partner = list(filter(
    #                 lambda x: x.get('account_id') == account.id and \
    #                     x.get('partner_id') == pid,
    #                 datas_by_account
    #             ))
    #             if datas_by_partner:
    #                 partner = partners.filtered(lambda p: p.id == pid)
    #                 initial = datas_by_partner[0].get('initial') or 0
    #                 final = datas_by_partner[0].get('final') or 0
    #                 debit = sum(x.get('debit') for x in datas_by_partner)
    #                 credit = sum(x.get('credit') for x in datas_by_partner)
    #                 acc_initial += initial
    #                 acc_final += final
    #                 acc_debit += debit
    #                 acc_credit += credit
    #                 # Add group by account and partner
    #                 values = {
    #                     'bold': True,
    #                     'group': False,
    #                     'account_id': account.id,
    #                     'code': account.code,
    #                     'name': account.name,
    #                     'partner_id': '',
    #                     'vat': partner.vat,
    #                     'partner': partner.name or '++',
    #                     'date': '',
    #                     'journal': '',
    #                     'move': '',
    #                     'line': '',
    #                 }
    #                 if self.currency_by:
    #                     values.update({
    #                         'currency': '',
    #                         'amount': '',
    #                     })
    #                 values.update({
    #                     'initial': initial,
    #                     'debit': debit,
    #                     'credit': credit,
    #                     'final': final,
    #                 })
    #                 query_data.append(values)
    #         # Add group by account
    #         values = {
    #             'bold': True,
    #             'group': False,
    #             'account_id': account.id,
    #             'code': account.code,
    #             'name': account.name,
    #             'partner_id': '',
    #             'vat': '',
    #             'partner': '',
    #             'date': '',
    #             'journal': '',
    #             'move': '',
    #             'line': '',
    #         }
    #         if self.currency_by:
    #             values.update({
    #                 'currency': '',
    #                 'amount': '',
    #             })
    #         values.update({
    #             'initial': acc_initial,
    #             'debit': acc_debit,
    #             'credit': acc_credit,
    #             'final': acc_final,
    #         })
    #         query_data.append(values)

    #         # domain = [
    #         #     ('partner_id', '!=', False),
    #         #     ('date', '<', self.date_from),
    #         # ]
    #         # if self.line_state:
    #         #     domain.append(('parent_state', '=', 'posted'))

    #         # if self.partners_ids:
    #         #     domain.append(('partner_id', 'in', self.partners_ids.ids))

    #         # domain.append(('account_id', '=', account.id))

    #         # lines = Line.search(domain)

    #         # datas = [
    #         #   rd for rd in copy_data if rd.get('account_id') == account.id
    #         # ]
    #         # debit_credit_fields = self.report_type == 'local' and \
    #         #     ['debit','credit'] or \
    #         #     ['ifrs_debit','ifrs_credit']
    #         # initial = sum(
    #         #     lines.mapped(debit_credit_fields[0])
    #         # ) - sum(
    #         #     lines.mapped(debit_credit_fields[1])
    #         # )
    #         # debit = sum(d.get('debit') for d in datas)
    #         # credit = sum(d.get('credit') for d in datas)
    #         # final = initial + (debit - credit)
    #         # values = {
    #         #     'bold': True,
    #         #     'group': False,
    #         #     'account_id': account.id,
    #         #     'code': account.code,
    #         #     'name': account.name,
    #         #     'vat': '',
    #         #     'partner': '',
    #         #     'date': '',
    #         #     'journal': '',
    #         #     'move': '',
    #         #     'line': '',
    #         # }
    #         # if self.currency_by:
    #         #     values.update({
    #         #         'currency': '',
    #         #         'amount': '',
    #         #     })
    #         # values.update({
    #         #     'initial': initial,
    #         #     'debit': debit,
    #         #     'credit': credit,
    #         #     'final': final,
    #         # })
    #         # query_data.append(values)
    #         if self.group_by_partner:
    #             partner_lines = self.group_total_amounts_for_partners(
    #                   copy_data, account)
    #             query_data = query_data + partner_lines
    #     if self.group_by:
    #         copy_data = list(query_data)
    #         aids = [cp.get('account_id') for cp in copy_data]
    #         aids = list(set(aids))
    #         accounts = self.env['account.account'].browse(aids)
    #         groups = accounts.group_id
    #         for group in groups:
    #             aids = group.account_ids.ids
    #             datas = [
    #                 cp for cp in copy_data if not cp.get('partner') and \
    #               cp.get('account_id') in aids
    #             ]
    #             values = {
    #                 'bold': True,
    #                 'group': True,
    #                 'account_id': group.id,
    #                 'code': group.code,
    #                 'name': group.name,
    #                 'vat': '',
    #                 'partner': '',
    #                 'date': '',
    #                 'journal': '',
    #                 'move': '',
    #                 'line': '',
    #             }

    #             if self.currency_by:
    #                 values.update({
    #                     'currency': '',
    #                     'amount': '',
    #                 })

    #             values.update({
    #                 'initial': sum(d.get('initial') for d in datas),
    #                 'debit': sum(d.get('debit') for d in datas),
    #                 'credit': sum(d.get('credit') for d in datas),
    #                 'final': sum(d.get('final') for d in datas),
    #             })

    #             query_data.append(values)

    #         parents=groups.parent_id
    #         while parents:
    #             new_data=list(query_data)
    #             for parent in parents:
    #                 cids=parent.child_ids.ids
    #                 datas=[
    #                     nd for nd in new_data if nd.get('group') and \
    #               nd.get('account_id') in cids
    #                 ]
    #                 values={
    #                     'bold': True,
    #                     'group': True,
    #                     'account_id': parent.id,
    #                     'code': parent.code,
    #                     'name': parent.name,
    #                     'vat': '',
    #                     'partner': '',
    #                     'date': '',
    #                     'journal': '',
    #                     'move': '',
    #                     'line': '',
    #                 }

    #                 if self.currency_by:
    #                     values.update({
    #                         'currency': '',
    #                         'amount': '',
    #                     })

    #                 values.update({
    #                     'initial': sum(d.get('initial') for d in datas),
    #                     'debit': sum(d.get('debit') for d in datas),
    #                     'credit': sum(d.get('credit') for d in datas),
    #                     'final': sum(d.get('final') for d in datas),
    #                 })

    #                 query_data.append(values)

    #             parents=parents.parent_id

    #     query_data=sorted(
    #         query_data,
    #         key=lambda r: [r.get('code'), r.get('partner')]
    #     )

    #     return {'report_data': query_data and query_data or []}

    def prepare_data_query(self):
        query = self.prepare_query()
        self.env.cr.execute(query)
        data_query = self.env.cr.dictfetchall()
        return data_query

    def prepare_query(self):
        query = """
        select
            False as bold,
            False as group,
            aa.id as account_id,
            aa.code as code,
            aa.name as name,
            aml.partner_id as partner_id,
            rp.vat as vat,
            coalesce(rp.name, '**') as partner,
            aml.date as date,
            aj.name as journal,
            am.name as move,
            aml.name as line,
        """

        if self.currency_by:
            query += """
                rc.name as currency,
                aml.amount_currency as amount,
            """

        query += """
            coalesce((
                select sum(aml2.debit - aml2.credit)
                from account_move_line as aml2
                where aml2.account_id = aml.account_id
                and (
                    aml2.partner_id = aml.partner_id
                    or
                    (
                        aml2.partner_id is null
                        and
                        aml.partner_id is null
                    )
                )
                and aml2.date < '{date_start}'
            ), 0) as initial,
            coalesce(aml.{debit}, 0) as debit,
            coalesce(aml.{credit}, 0) as credit,
            coalesce((
                select sum(aml2.debit - aml2.credit)
                from account_move_line as aml2
                where aml2.account_id = aml.account_id
                and (
                    aml2.partner_id = aml.partner_id
                    or
                    (
                        aml2.partner_id is null
                        and
                        aml.partner_id is null
                    )
                )
                and aml2.date <= '{date_end}'
            ), 0) as final
        from account_move_line aml
        inner join account_account aa on aa.id = aml.account_id
        inner join account_move am on am.id = aml.move_id
        inner join account_journal aj on aj.id = aml.journal_id
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
        """ % (
            self.date_from,
            self.date_to,
        )

        if self.line_state:
            query += """
            and aml.parent_state = 'posted'
            """

        if self.report_type == 'ifrs':
            query += """
            and aml.ifrs_type != 'local'
            """
        else:
            query += """
            and aml.ifrs_type != 'ifrs'
            """

        if self.accounts_ids:
            accounts_ids = self.accounts_ids.ids
            aids = str(tuple(accounts_ids)).replace(',)', ')')
            query += """
            and aml.account_id in %s
            """ % aids

        if self.partners_ids:
            partners_ids = self.partners_ids.ids
            pids = str(tuple(partners_ids)).replace(',)', ')')
            query += """
            and aml.partner_id in %s
            """ % pids

        query += """
        order by aml.date, am.name, rp.name
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
        ]
        if self.account_analityc:
            report_header += [
                ('analytic', _('Account Analytic')),
            ]

        report_header += [
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


    def preview_html(self):
        self.ensure_one()
        action_report = self.env["ir.actions.report"].search(
            [
                ("report_name",
                 "=",
                 'report_auxiliary.auxiliary_template'),
                ("report_type",
                 "=",
                 'qweb-html')
            ],
            limit=1,
        )
        if not action_report:
            raise ValidationError(_(
                'Not found report ID: '
                'account_report.account_auxiliary_template'
            ))
        data_report = {}
        out = action_report.report_action(self, data=data_report)
        return out

    def data_report_preview(self):
        self.ensure_one()
        header = self.prepare_header()
        data = self.prepare_data2()

        report_name = self.report_type == 'local' and \
            _('Libro Auxiliar') or \
            _('Libro Auxiliar NIIF')
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
                elif k in ('group', 'account_id'):
                    continue
                else:
                    class_span = ' '.join([
                        bold and
                        'bold-cell-report back-cell' or
                        'normal-cell-report',
                        k in ('initial', 'debit', 'credit',
                              'final') and 'amount' or 'left'
                    ])
                    tr_text += '<div class="act_as_cell %s">%s</div>' % (
                        class_span,
                        type(v) in (type(2), type(2.3)) and \
                        '{:_.2f}'.format(v).replace('.',',').replace('_','.') or \
                        v or ''
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
