# -*- coding: utf-8 -*-


from odoo import fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
import datetime
import xlsxwriter
from io import BytesIO
import io


class ReportInvoice(models.TransientModel):
    _name = "report.margen.product"
    _description = 'Reporte de margen de productos'
    
    name = fields.Char('Nombre', default='Informe de Margen de Producto', readonly=True)
    date_from = fields.Date('Desde', required=True, default=(fields.Date.today() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Date.today()))
    product_ids = fields.Many2many('product.product', string='Productos', copy=False) 
    brand_ids = fields.Many2many('product.brand', string='Marcas')
    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    

    def compute_report(self):
        def _add_where(table, fld, vl):
            return f" AND {table}.{fld} IN ({','.join(str(x.id) for x in vl)})"
        
        cr = self._cr
        wh = ''
        uid = self.env.user.id
        dt_now = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        wh = '' 
        if self.product_ids:
            wh += _add_where('sol', 'product_id', self.product_ids)
        if self.brand_ids:
            wh += _add_where('pt', 'product_brand_id', self.brand_ids)

            
        #add_fields_insert, add_fields_select, add_fields_from = self.extended_compute_fields()
            
        cr.execute(f'DELETE FROM margen_report_line')
            
        qry = f'''
                INSERT INTO margen_report_line (product_id, default_code, product_brand_id, quantity, price_subtotal, cost, utility, 
                                                percentage_uti, percentage_renta, create_date, write_date)

                SELECT
                    aml.product_id, 
                    pt.default_code,
                    pt.product_brand_id,
                    SUM(aml.quantity * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) AS num_qty,
                    SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) AS subtotal,
                    svl.cost_in - svl.cost_off  AS cost_product,
                    (SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) AS difference,
                    ((SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) / 
                    NULLIF(SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)),0)) AS utility,
                    ((SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) / 
                    NULLIF((svl.cost_in - svl.cost_off),0)) AS renta,
                    '{dt_now}', 
                    '{dt_now}'

                FROM 
                    account_move_line aml
                    LEFT JOIN account_move am ON aml.move_id = am.id
                    LEFT JOIN product_product pp ON aml.product_id = pp.id
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN product_brand pb ON pt.product_brand_id = pb.id
                    LEFT JOIN LATERAL (
                                SELECT 
                                    CASE 
                                        WHEN svl.value >= 0 THEN SUM(svl.value * (-1))
                                        ELSE 0
                                    END AS cost_off,
                                    CASE 
                                        WHEN svl.value < 0 THEN SUM(ABS(svl.value)) 
                                        ELSE 0
                                    END AS cost_in

                                FROM 
                                    stock_valuation_layer svl
                                WHERE 
                                    svl.product_id = pp.id AND
                                    DATE(svl.create_date) BETWEEN  '{dt_from}' AND '{dt_to}' 
                                GROUP BY
                                svl.value

                                LIMIT 1
                    ) svl ON true

                    WHERE
                        am.move_type IN ('out_invoice', 'out_refund') AND
                        pt.detailed_type = 'product' AND 
                        am.state = 'posted' AND
                        am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' 
                        {wh}
                    GROUP BY 
                        aml.product_id,
                        pt.default_code,
                        pt.product_brand_id,
                        svl.cost_in,
                        svl.cost_off
                        
                   '''     
        cr.execute(qry)

    def analysis(self):
        self.compute_report()
        view_id = self.env['ir.ui.view'].search([('name','=','report_margen_product.view_margen_report_line_pivot')])
        return {
                'name': 'Margen de productos',
                'view_type': 'form',
                'view_mode': 'pivot',
                'view_id': view_id.id, 
                'res_model': 'margen.report.line',
                'type': 'ir.actions.act_window'
            }

    def _compute_excel(self):
        def _add_where(table, fld, vl):
            return f" AND {table}.{fld} IN ({','.join(str(x.id) for x in vl)})"
    
        #APLICAR FILTROS
        wh = '' 
        if self.product_ids:
            wh += _add_where('sol', 'product_id', self.product_ids)
        if self.brand_ids:
            wh += _add_where('pt', 'product_brand_id', self.brand_ids)

        cr = self.env.cr
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        cr.execute(f'''SELECT
                            pt.name, 
                            pt.default_code,
                            pb.name,
                            SUM(aml.quantity * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) AS num_qty,
                            SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) AS subtotal,
                            svl.cost_in - svl.cost_off  AS cost_product,
                            (SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) AS difference,
                            ((SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) / 
                            NULLIF(SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)),0)) AS utility,
                            ((SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) - (svl.cost_in - svl.cost_off)) / 
                            NULLIF((svl.cost_in - svl.cost_off),0)) AS renta
                            

                        FROM account_move_line aml
                            LEFT JOIN account_move am ON aml.move_id = am.id
                            LEFT JOIN product_product pp ON aml.product_id = pp.id
                            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN product_brand pb ON pt.product_brand_id = pb.id
                            LEFT JOIN LATERAL (
                                SELECT 
                                    CASE 
                                        WHEN svl.value >= 0 THEN SUM(svl.value) * (-1)
                                        ELSE 0
                                    END AS cost_off,
                                    CASE 
                                        WHEN svl.value < 0 THEN SUM(ABS(svl.value)) 
                                        ELSE 0
                                    END AS cost_in

                                FROM 
                                    stock_valuation_layer svl
                                WHERE 
                                    svl.product_id = pp.id AND
                                    DATE(svl.create_date) BETWEEN  '{dt_from}' AND '{dt_to}' 
                                GROUP BY
                                    svl.value

                                LIMIT 1
                            ) svl ON true


                        WHERE
                            am.move_type IN ('out_invoice', 'out_refund') AND
                            pt.detailed_type = 'product' AND 
                            am.state = 'posted' AND
                            am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' 
                            {wh}
                        GROUP BY 
                        pt.name,
                        pt.default_code,
                        pb.name,
                        svl.cost_in,
                        svl.cost_off                  
                        
                        
                      ''')
        result = cr.fetchall()
        return result
        
    def get_xlsx_report(self):
        result = self._compute_excel()
        output = io.BytesIO()
        titles = [
                'Producto', 
                'Referencia Interna',
                'Marca',
                'Cantidad',
                'Ingreso', 
                'Costo',
                'Utilidad', 
                '%Rentabilidad', 
                '%Utilidad'
                ]
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()

        # Formants
        titles_format = workbook.add_format()
        titles_format.set_align("center")
        titles_format.set_bold()
        money_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        worksheet.set_column("A:I", 22)
        worksheet.set_row(0, 25)
        
        col_num = 0
        for title in titles:
            worksheet.write(0, col_num, title, titles_format)
            col_num += 1
        
        for index, data in enumerate(result):
            row = index + 1
            col_num = 0
            for i, d in enumerate(data):
                if i in [4,5, 6]:
                    worksheet.write(row, col_num, d, money_format)
                else:
                    worksheet.write(row, col_num, d)
                col_num += 1
            

        
        workbook.close()
        xlsx_data = output.getvalue()

        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "report_margen.xlsx"

class InvoiceReportLine(models.TransientModel):
    _name = "margen.report.line"
    _description = "Lineas de reporte de Margen de productos"
    

    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    quantity = fields.Float(string='Cantidad Facturada', readonly=True)
    cost = fields.Float(string='Costo', readonly=True)
    utility = fields.Float(string='Utilidad', readonly=True)
    percentage_uti = fields.Float(string='%Rentabilidad', digits=(1,2), readonly=True)
    percentage_renta = fields.Float(string='%Utilidad', digits=(1,2), readonly=True)
    price_subtotal = fields.Float(string='V. antes Impuesto', readonly=True)
    default_code = fields.Char('Referencia interna', readonly=True)
    product_brand_id = fields.Many2one('product.brand', string="Marca", readonly=True)
    
    