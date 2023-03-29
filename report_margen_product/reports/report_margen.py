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
    date_from = fields.Date('Desde', required=True, default=(fields.Datetime.now() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Datetime.now()).date())
    product_ids = fields.Many2many('product.product', string='Productos', copy=False) 
    brand_ids = fields.Many2many('product.brand', string='Marcas')
    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    

    def _compute_excel(self):
        def _add_wh(fld, tbl):
            return " AND {} IN ({})".format(fld, ','.join(str(x.id) for x in tbl))
    
        #APLICAR FILTROS
        wh = '' 
        if self.product_ids:
            wh += _add_wh('sol.product_id', self.product_ids)
        if self.product_ids:
            wh += _add_wh('pt.product_brand_id', self.brand_ids)

        cr = self.env.cr
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        cr.execute(f'''SELECT
                            pt.name, 
                            pb.name,
                            SUM(sol.product_uom_qty) qty, 
                            SUM(sol.price_subtotal) price,
                            svl.unit_cost*(SUM(sol.product_uom_qty)) AS cost,
                            SUM(sol.price_subtotal) - svl.unit_cost*(SUM(sol.product_uom_qty)),
                            (SUM(sol.price_subtotal) - svl.unit_cost*SUM(sol.product_uom_qty)) / SUM(sol.price_subtotal),
                            (SUM(sol.price_subtotal) - svl.unit_cost*SUM(sol.product_uom_qty)) / (svl.unit_cost*(SUM(sol.product_uom_qty)))

                        FROM sale_order_line sol
                            INNER JOIN sale_order so ON sol.order_id = so.id 
                            INNER JOIN product_product pp ON sol.product_id = pp.id 
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            INNER JOIN stock_move sm ON sol.id = sm.sale_line_id 
                            LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
                            LEFT JOIN product_brand pb ON pb.id = pt.product_brand_id

                        WHERE
                            so.state = 'done' AND
                            so.date_order BETWEEN   '{dt_from}' AND '{dt_to}' {wh}
                        GROUP BY
                        pt.name,
                        pb.name,
                        svl.unit_cost
                      ''')
        result = cr.fetchall()
        return result
        
    def get_xlsx_report(self):
        result = self._compute_excel()
        output = io.BytesIO()
        titles = [
                'Producto', 
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
        worksheet.set_column("A:H", 22)
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
        self.xls_filename = "report_invoice.xlsx"
    
    
    


    