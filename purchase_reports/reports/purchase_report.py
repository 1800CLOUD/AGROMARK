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
    date_from = fields.Date('Desde', required=True, default=(fields.Date.today() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Date.today()))

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
            
        cr.execute(f'DELETE FROM report_purchase_line')
            
        qry = f'''
            INSERT INTO report_purchase_line (invoice_date, partner_vat, partner_id, purchase_id, invoice_id, journal_id, default_code, 
                        product_id, account_id, amount_untaxed, tax_id, value_tax, amount_total, move_type, product_type, create_date, write_date)
                SELECT
                    am.invoice_date,
                    rp.vat, 
                    am.partner_id, 
                    po.id, 
                    aml.move_id,  
                    am.journal_id,
                    pt.default_code, 
                    aml.product_id,
                    aml.account_id,
                    aml.balance,
                    at.tax,
                    CASE 
                        WHEN am.move_type = 'in_refund' THEN at.value * (-1)
                        ELSE at.value
                    END,
                    CASE
                        WHEN am.move_type = 'in_refund' THEN am.amount_total * (-1)
                        ELSE am.amount_total 
                    END,
                    am.move_type,
                    pt.detailed_type,
                    '{dt_now}', 
                    '{dt_now}'

                
            FROM
                account_move_line aml
                LEFT JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN purchase_order po ON po.id = am.order_purchase_id
                LEFT JOIN res_partner rp ON am.partner_id = rp.id
                INNER JOIN product_product pp ON aml.product_id = pp.id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN LATERAL(
                                SELECT
                                    CASE 
                                        WHEN dt.id = 1 THEN amltax.account_tax_id
                                        ELSE NULL
                                    END AS tax,
                                    CASE
                                        WHEN dt.id = 1 THEN SUM((at.amount * aml.price_subtotal)/100)
                                        ELSE NULL
                                    END AS value
                                FROM
                                    account_move_line_account_tax_rel amltax
                                LEFT JOIN account_tax at ON amltax.account_tax_id = at.id
                                LEFT JOIN dian_tax_type dt ON at.dian_tax_type_id = dt.id
                                WHERE amltax.account_move_line_id = aml.id
                                GROUP BY 
                                dt.id,
                                amltax.account_tax_id
                                LIMIT 1
                ) at ON true
                
                 

            WHERE 
                am.move_type IN ('in_invoice', 'in_refund', 'in_receipt') AND
                am.state = 'posted' AND
                am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}'
                {wh}
                
                GROUP BY 
                am.invoice_date,
                rp.vat,
                am.partner_id,
                po.id, 
                am.id,  
                am.journal_id, 
                pt.default_code,
                aml.product_id,
                aml.account_id,
                am.move_type,
                pt.detailed_type,
                aml.balance,
                at.tax,
                at.value,
                aml.id
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
                am.invoice_date,
                am.name,
                aj.name,  
                pt.default_code,
                pt.name,
                aa.code, 
                aml.balance,
                at.tax,
                at.value,
                CASE
                    WHEN am.move_type = 'in_refund' THEN am.amount_total * (-1)
                    ELSE am.amount_total 
                END
        
            FROM
                account_move_line aml
                LEFT JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN purchase_order po ON po.id = am.order_purchase_id
                LEFT JOIN res_partner rp ON am.partner_id = rp.id
                INNER JOIN product_product pp ON aml.product_id = pp.id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN LATERAL(
                                SELECT
                                    CASE 
                                        WHEN dt.id = 1 THEN STRING_AGG(at.description, ';')
                                        ELSE ''
                                    END AS tax,
                                    CASE
                                        WHEN dt.id = 1 THEN SUM((at.amount * aml.price_subtotal)/100)
                                        ELSE NULL
                                    END AS value
                                FROM
                                    account_move_line_account_tax_rel amltax
                                LEFT JOIN account_tax at ON amltax.account_tax_id = at.id
                                LEFT JOIN dian_tax_type dt ON at.dian_tax_type_id = dt.id
                                WHERE amltax.account_move_line_id = aml.id
                                GROUP BY 
                                dt.id
                                LIMIT 1
                ) at ON true
                LEFT JOIN account_journal aj ON aml.journal_id = aj.id
                LEFT JOIN account_account aa ON aml.account_id = aa.id 

            WHERE 
                am.move_type IN ('in_invoice', 'in_refund', 'in_receipt') AND
                am.state = 'posted' AND
                am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}'
                {wh}
            GROUP BY 
                am.invoice_date,
                am.name,
                pt.name,
                pt.default_code,
                rp.vat,
                rp.name,
                po.name,
                am.invoice_date,
                am.name,
                aj.name,
                aa.code,
                at.tax,
                at.value,
                am.move_type,
                am.amount_total,
                aml.balance,
                aml.id
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
                  'FECHA FACTURA',
                  'FACTURA',
                  'DIARIO',
                  'REFERENCIA INTERNA',
                  'PRODUCTO',
                  'CUENTA',
                  'VALOR A. IMPUESTO', 
                  'VALOR IVA',
                  'TARIFA IVA',
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
        money_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        col_num = 0
        for title in titles:
            worksheet.write(0, col_num, title, titles_format)
            col_num += 1
        
        for index, data in enumerate(result):
            row = index + 1
            col_num = 0
            for i, d in enumerate(data):
                if i in [9,11, 12]:
                    worksheet.write(row, col_num, d, money_format)
                else:
                    worksheet.write(row, col_num, d)
                if isinstance(d, datetime.date):
                    d = d.strftime("%Y-%m-%d")
                    worksheet.write(row, col_num, d)
                col_num += 1
            
        
        workbook.close()
        xlsx_data = output.getvalue()

        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "report_purchase.xlsx"

    
    def button_bi(self):
        self.compute_report()
        view_id = self.env['ir.ui.view'].search([('name','=','purchase_reports.report_purchase_line_pivot')])
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        domain = [('invoice_date', '>', dt_from), ('invoice_date', '<=', dt_to)]
        return {
                'domain': domain,
                'name': 'Análisis de Facturados',
                'view_type': 'form',
                'view_mode': 'pivot',
                'view_id': view_id.id, 
                'res_model': 'report.purchase.line',
                'type': 'ir.actions.act_window'
            }
    
    
class ReportPurchaseLine(models.Model):
    _name = 'report.purchase.line'
    _description = 'Lineas del reporte de compras'
    
    
    
    partner_id = fields.Many2one('res.partner', 'Proveedor', copy=False, readonly=True)
    partner_vat = fields.Char('NIT', copy=False, readonly=True, index=True)
    invoice_date = fields.Date(readonly=True, string="Fecha de Factura", copy=False, index=True)
    default_code = fields.Char('Referencia Interna', copy=False, readonly=True, index=True)
    invoice_id = fields.Many2one('account.move', string="Factura", copy=False, readonly=True)
    purchase_id = fields.Many2one('purchase.order', 'Orden de compra', copy=False, readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', copy=False, readonly=True)
    journal_id = fields.Many2one('account.journal', 'Diario', copy=False, readonly=True)
    account_id = fields.Many2one('account.account', 'Cuenta', copy=False, readonly=True)
    amount_untaxed = fields.Float('Valor A. impuesto', copy=False, readonly=True)
    tax_id = fields.Many2one('account.tax', 'Impuesto', copy=False, readonly=True)
    amount_total = fields.Float('Valor total', copy=False, readonly=True)
    value_tax = fields.Float('Valor Iva', copy=False, readonly=True)
    move_type = fields.Selection([
        ('in_invoice', 'Factura Proveedor'),
        ('in_refund', 'Factura rectificativa'),
        ], string='Tipo de Factura', readonly=True)
    product_type = fields.Selection([
        ('product', 'Almacenable'),
        ('service', 'Servicio'),
        ('consu', 'Consumible'),
        ], string='Tipo de producto', readonly=True)
    