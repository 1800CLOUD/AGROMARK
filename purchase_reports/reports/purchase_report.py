# -- coding: utf-8 --

from odoo import fields, models

from dateutil.relativedelta import relativedelta
import base64
import datetime
import xlsxwriter
from io import BytesIO
import io


class ReportPurchase(models.TransientModel):
    _name = 'report.purchase'
    _description = 'Reporte Disponibilidad Stock'
    
    name = fields.Char('Nombre', readonly=True, default='Reporte de compras')
    partner_ids = fields.Many2many('res.partner', string='Proveedores', copy=False)
    date_from = fields.Datetime('Desde', required=True, default=(fields.Datetime.now() - relativedelta(month=1)))
    date_to = fields.Datetime('Hasta', required=True, default=(fields.Datetime.now()))

    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    
    
    # noinspection PyMethodMayBeStatic
    def extended_compute_fields(self):
        """
        inherit on extended modules
        """
        add_fields_insert = add_fields_select = add_fields_from = ''
        return add_fields_insert, add_fields_select, add_fields_from
    
    def compute_report(self):
        def _add_where(table, fld, vl):
            return f" AND {table}.{fld} IN ({','.join(str(x.id) for x in vl)})"
        
        cr = self._cr
        wh = ''
        uid = self.env.user.id
        dt_now = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        if self.partner_ids:
            wh += _add_where('rp', 'partner_id', self.partner_ids)


            
        #add_fields_insert, add_fields_select, add_fields_from = self.extended_compute_fields()
            
        cr.execute(f'DELETE FROM report_purchase_line WHERE create_uid = {uid}')
            
        qry = f'''
            INSERT INTO report_purchase_line (partner_vat, partner_id, purchase_id, invoice_id, journal_id, amount_untaxed,
                        tax_id, amount_total, create_date, write_date)
                SELECT
                    rp.vat, 
                    po.partner_id, 
                    am.order_purchase_id, 
                    am.id,  
                    am.journal_id, 
                    CASE 
                    WHEN am.move_type = 'in_refund' THEN am.amount_untaxed * (-1)
                    ELSE am.amount_untaxed END,
                    at.id,
                    CASE
                    WHEN am.move_type = 'in_refund' THEN am.amount_total * (-1)
                    ELSE am.amount_total END,
                    '{dt_now}', 
                    '{dt_now}'

                FROM
                    purchase_order po
                    INNER JOIN account_move am ON po.id = am.order_purchase_id
                    INNER JOIN account_journal aj ON am.journal_id = aj.id
                    INNER JOIN res_partner rp ON po.partner_id = rp.id
                    LEFT JOIN account_move_line aml ON am.id = aml.move_id
                    LEFT JOIN account_tax at ON aml.tax_line_id = at.id 
        

                WHERE
                    am.state = 'posted' AND
                    am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}'
                    {wh}
                GROUP BY 
                rp.vat,
                po.partner_id, 
                am.id,  
                am.journal_id, 
                aj.name,
                am.move_type,
                am.amount_untaxed,
                at.id,
                am.amount_total
        '''
        cr.execute(qry)
        
    
    def _button_excel(self):
        def _add_where(table, fld, vl):
            return f" AND {table}.{fld} IN ({','.join(str(x.id) for x in vl)})"
        
        uid = self.env.user.id
        cr = self._cr
        wh = ''
        uid = self.env.user.id
        dt_now = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        if self.partner_ids:
            wh += _add_where('rp', 'partner_id', self.partner_ids)

        
        excel_qry = f'''            
            SELECT 
                rp.vat, 
                rp.name, 
                po.name, 
                am.name, 
                aj.name, 
                CASE 
                WHEN am.move_type = 'in_refund' THEN am.amount_untaxed * (-1)
                ELSE am.amount_untaxed END,
                STRING_AGG(at.description, ';'),
                CASE
                WHEN am.move_type = 'in_refund' THEN am.amount_total * (-1)
                ELSE am.amount_total END
        
            FROM
                report_purchase_line rpl
                INNER JOIN purchase_order po ON rpl.purchase_id = po.id
                LEFT JOIN res_partner rp ON rpl.partner_id = rp.id
                LEFT JOIN account_move am ON rpl.invoice_id = am.id
                LEFT JOIN account_move_line aml ON am.id = aml.move_id
                LEFT JOIN account_tax at ON aml.tax_line_id = at.id 
                LEFT JOIN dian_tax_type dt ON at.dian_tax_type_id = dt.id 
                LEFT JOIN account_journal aj ON rpl.journal_id = aj.id

            WHERE 
                am.state = 'posted' AND
                am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}'
                {wh}
            GROUP BY 
                rp.vat,
                rp.name,
                po.name,
                am.name,
                aj.name,
                am.move_type,
                am.amount_untaxed,
                am.amount_total
        '''
        cr.execute(excel_qry)
        result = cr.fetchall()

        return result

    def get_xlsx_report(self):
        result = self._button_excel()
        output = io.BytesIO()
        titles = ['NIT', 
                  'PROVEEDOR', 
                  'ORDEN DE COMPRA', 
                  'FACTURA',
                  'DIARIO', 
                  'VALOR A. IMPUESTO', 
                  'TARIFA IMPUESTO',
                  'VALOR TOTAL'
                  ]
    
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()

        # Formants
        titles_format = workbook.add_format()
        titles_format.set_align("center")
        titles_format.set_bold()
        worksheet.set_column("A:G", 22)
        worksheet.set_row(0, 25)
        
        col_num = 0
        for title in titles:
            worksheet.write(0, col_num, title, titles_format)
            col_num += 1
        
        for index, data in enumerate(result):
            row = index + 1
            col_num = 0
            for d in data:
                if isinstance(d, datetime.date):
                    d = d.strftime("%Y-%m-%d")
                worksheet.write(row, col_num, d)
                col_num += 1
        
        workbook.close()
        xlsx_data = output.getvalue()

        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "report_stock.xlsx"

    
    def button_bi(self):
        self.compute_report()
        return_dict = {}
        if 'pivot' in self._context:
            view_id = self.env['ir.ui.view'].search([('name','=','report_purchase_line_pivot')], limit=1)
            return_dict.update({'view_mode': 'pivot'})
        else:
            view_id = self.env['ir.ui.view'].search([('name','=','report_purchase_line_pivot')], limit=1)
            search_view_id = self.env['ir.ui.view'].search([('name','=','report_purchase_line_search')], limit=1)
            return_dict.update({
                'search_view_id': search_view_id.id,
                'view_mode': 'tree'})
        return_dict.update({
            'name': 'Informe de compras',
            'view_type': 'pivot',
            'view_id': view_id.id,
            'res_model': 'report.purchase.line',
            'type': 'ir.actions.act_window',
        })
        return return_dict
    
    
class ReportPurchaseLine(models.Model):
    _name = 'report.purchase.line'
    _description = 'Lineas del reporte de compras'
    _report_vacuum = True
    
    
    partner_id = fields.Many2one('res.partner', 'Proveedor', copy=False, readonly=True, required=True)
    partner_vat = fields.Char('NIT', copy=False, readonly=True, index=True)
    invoice_id = fields.Many2one('account.move', 'Factura', copy=False, readonly=True, required=True)
    purchase_id = fields.Many2one('purchase.order', 'Orden de compra', copy=False, readonly=True, required=True)
    journal_id = fields.Many2one('account.journal', 'Diario', copy=False, readonly=True, required=True)
    amount_untaxed = fields.Float('Valor A. impuesto', copy=False, readonly=True, required=True)
    tax_id = fields.Many2one('account.tax', 'Impuesto', copy=False, readonly=True, index=True )
    amount_total = fields.Float('Valor total', copy=False, readonly=True, required=True)
    