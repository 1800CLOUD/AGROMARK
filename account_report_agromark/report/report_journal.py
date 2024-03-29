import time
from odoo import api, models, _
from odoo.exceptions import UserError

class CustomReportJournal(models.AbstractModel):
    _inherit = "report.account.report_journal"

    def lines(self, target_move, journal_ids, sort_selection, data):
        if isinstance(journal_ids, int):
            journal_ids = [journal_ids]

        move_state = ['draft', 'posted', 'cancel']
        if target_move == 'posted':
            move_state = ['posted']
        else:
            move_state = ['draft', 'posted', 'cancel']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_ids)] + query_get_clause[2]
        query = '''
                SELECT "account_move_line".id
                FROM {0}
                LEFT JOIN account_move am ON "account_move_line".move_id = am.id
                LEFT JOIN account_account acc ON "account_move_line".account_id = acc.id
                WHERE am.state IN %s 
                AND am.journal_id IN %s
                AND {1}
                ORDER BY
                '''.format(query_get_clause[0], query_get_clause[1])
        #query = 'SELECT "account_move_line".id FROM ' + query_get_clause[0] + ' LEFT JOIN account_move am ON "account_move_line".move_id=am.id LEFT JOIN account_account acc ON "account_move_line".account_id = acc.id WHERE am.state IN %s AND "account_move_line".journal_id IN %s AND ' + query_get_clause[1] + ' ORDER BY '
        if sort_selection == 'date':
            query += '"account_move_line".date'
        else:
            query += 'am.name'
        query += ', "account_move_line".move_id, acc.code'
        self.env.cr.execute(query, tuple(params))
        ids = (x[0] for x in self.env.cr.fetchall())
        return self.env['account.move.line'].browse(ids)

    def _sum_debit(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']
        else:
            move_state = ['draft', 'posted', 'cancel']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id.ids)] + query_get_clause[2]
        query = '''
                SELECT COALESCE(SUM("account_move_line".debit), 0.0)
                FROM {0}
                LEFT JOIN account_move_line aml ON "account_move_line".move_id = {0}.id
                LEFT JOIN account_move am ON {0}.move_id = am.id
                WHERE am.state IN %s
                    AND am.journal_id IN %s
                    AND {1}
                '''.format(query_get_clause[0], query_get_clause[1])

        self.env.cr.execute(query, tuple(params))
        return self.env.cr.fetchone()[0]

    def _sum_credit(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']
        else:
            move_state = ['draft', 'posted', 'cancel']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id.ids)] + query_get_clause[2]
        query = '''
                SELECT COALESCE(SUM("account_move_line".credit), 0.0)
                FROM {0}
                LEFT JOIN account_move_line aml ON "account_move_line".move_id = {0}.id
                LEFT JOIN account_move am ON {0}.move_id = am.id
                WHERE am.state IN %s
                    AND am.journal_id IN %s
                    AND {1}
                '''.format(query_get_clause[0], query_get_clause[1])

        self.env.cr.execute(query, tuple(params))
        return self.env.cr.fetchone()[0]

    def _get_taxes(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']
        else:
            move_state = ['draft', 'posted', 'cancel']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id.ids)] + query_get_clause[2]
        query = """
            SELECT rel.account_tax_id, SUM("account_move_line".balance) AS base_amount
            FROM account_move_line_account_tax_rel rel, """ + query_get_clause[0] + """ 
            LEFT JOIN account_move am ON "account_move_line".move_id = am.id
            WHERE "account_move_line".id = rel.account_move_line_id
                AND am.state IN %s
                AND am.journal_id IN %s
                AND """ + query_get_clause[1] + """
           GROUP BY rel.account_tax_id"""
        self.env.cr.execute(query, tuple(params))
        ids = []
        base_amounts = {}
        for row in self.env.cr.fetchall():
            ids.append(row[0])
            base_amounts[row[0]] = row[1]


        res = {}
        for tax in self.env['account.tax'].browse(ids):
            self.env.cr.execute('SELECT sum(debit - credit) FROM ' + query_get_clause[0] + ', account_move am '
                'WHERE "account_move_line".move_id=am.id AND am.state IN %s AND am.journal_id IN %s AND ' + query_get_clause[1] + ' AND tax_line_id = %s',
                tuple(params + [tax.id]))
            res[tax] = {
                'base_amount': base_amounts[tax.id],
                'tax_amount': self.env.cr.fetchone()[0] or 0.0,
            }
            if journal_id.type == 'sale':
                #sales operation are credits
                res[tax]['base_amount'] = res[tax]['base_amount'] * -1
                res[tax]['tax_amount'] = res[tax]['tax_amount'] * -1
        return res

   