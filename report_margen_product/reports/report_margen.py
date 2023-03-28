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
    
    name = fields.Char('Nombre', default='Informe de Margen de Producto', readonly=True)
    date_from = fields.Date('Desde', required=True, default=(fields.Datetime.now() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Datetime.now()).date())
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
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        dt_now = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.product_ids:
            wh += _add_where('sol', 'product_id', self.product_ids)

        if self.brand_ids:
            wh += _add_where('pt', 'product_brand_id', self.brand_ids)

            
        #add_fields_insert, add_fields_select, add_fields_from = self.extended_compute_fields()
            
        cr.execute(f'DELETE FROM report_margen_product_line WHERE create_uid = {uid}')
            
        qry = f'''
            INSERT INTO report_margen_product_line (product_id, product_brand_id, quantity, income, cost,
                utility, cost_effectiveness, margin_utility, create_date, write_date)
                    SELECT
                            sol.product_id, 
                            pt.product_brand_id,
                            SUM(sol.product_uom_qty), 
                            SUM(sol.price_subtotal),
                            svl.unit_cost*(SUM(sol.product_uom_qty)),
                            SUM(sol.price_subtotal) - svl.unit_cost*(SUM(sol.product_uom_qty)),
                            (SUM(sol.price_subtotal) - svl.unit_cost*SUM(sol.product_uom_qty)) / SUM(sol.price_subtotal),
                            (SUM(sol.price_subtotal) - svl.unit_cost*SUM(sol.product_uom_qty)) / (svl.unit_cost*(SUM(sol.product_uom_qty))),
                            '{dt_now}', 
                            '{dt_now}'

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
                        sol.product_id,
                        pt.product_brand_id,
                        svl.unit_cost
                        
        '''
        cr.execute(qry)
    

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
    
    def analysis(self):
        self.compute_report()
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        domain = [('date_order', '>', dt_from), ('date_order', '<=', dt_to)]
        return_dict = {}
        if 'pivot' in self._context:
            view_id = self.env['ir.ui.view'].search([('name','=','view_margen_report_pivot')], limit=1)
            return_dict.update({'view_mode': 'pivot'})
        else:
            view_id = self.env['ir.ui.view'].search([('name','=','view_margen_report_pivot')], limit=1)
            search_view_id = self.env['ir.ui.view'].search([('name','=','report_margen_product_line_search')], limit=1)
            return_dict.update({
                'search_view_id': search_view_id.id,
                'view_mode': 'pivot'})
        return_dict.update({
            'domain': domain,
            'name': 'Margen de producto',
            'view_type': 'pivot',
            'view_id': view_id.id,
            'res_model': 'report.margen.product.line',
            'type': 'ir.actions.act_window',
        })
        return return_dict
    

class ReportMargenProductLine(models.Model):
    _name = 'report.margen.product.line'
    _description = 'Lineas del reporte margen de productos'
    _order = 'product_id,income,cost,utility'
    _report_vacuum = True
    
    product_id = fields.Many2one('product.product', 'Producto', copy=False, readonly=True, required=True, index=True)
    product_brand_id = fields.Many2one(comodel_name="product.brand", string="Marca", copy=False, readonly=True, index=True)
    quantity = fields.Float('Cantidad', copy=False, readonly=True, required=True)
    income = fields.Float('Ingresos', copy=False, readonly=True, required=True)
    cost = fields.Float('Costo', copy=False, readonly=True, required=True)
    utility = fields.Float('Utilidad', copy=False, readonly=True, required=True)
    cost_effectiveness = fields.Float('rentabilidad', copy=False, readonly=True, required=True)
    margin_utility = fields.Float('Utilidad%', copy=False, readonly=True, required=True)
    