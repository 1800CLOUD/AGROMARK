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
                            SUM(aml.quantity * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END)) AS num_qty,
                            SUM(aml.price_subtotal * (CASE WHEN am.move_type = 'out_invoice' THEN 1 ELSE -1 END))
                            

                        FROM account_move_line aml
                            INNER JOIN account_move am ON aml.move_id = am.id
                            INNER JOIN product_product pp ON aml.product_id = pp.id
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            


                        WHERE
                            am.move_type IN ('out_invoice', 'out_refund') AND
                            pt.detailed_type = 'product' AND 
                            am.state = 'posted' AND
                            am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' 
                            {wh}
                        GROUP BY 
                        pt.name,
                        pt.default_code
                        
                        
                        
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
        worksheet.set_column("A:I", 22)
        worksheet.set_row(0, 25)
        
        col_num = 0
        for title in titles:
            worksheet.write(0, col_num, title, titles_format)
            col_num += 1
        
        for index, data in enumerate(result):
            row = index + 1
            col_num = 0
            for d in data:
                #if isinstance(d, datetime.date):
                #    d = d.strftime("%Y-%m-%d")
                worksheet.write(row, col_num, d)
                col_num += 1
        
        workbook.close()
        xlsx_data = output.getvalue()

        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "report_margen.xlsx"
    
    
    


    