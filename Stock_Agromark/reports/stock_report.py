# -- coding: utf-8 --

from odoo import fields, models
from odoo.addons import decimal_precision as dp
import base64
import datetime
import xlsxwriter
from io import BytesIO
import io


class ReportStockQuant(models.TransientModel):
    _name = 'report.stock.quant'
    _description = 'Reporte Disponibilidad Stock'
    
    name = fields.Char('Nombre', readonly=True, default='Reporte de Disponibilidad')
    location_ids = fields.Many2many('stock.location', string='Ubicaciones', copy=False, 
                                    domain="[('usage', '=', 'internal')]")
    product_ids = fields.Many2many('product.product', string='Productos', copy=False, 
                                   domain="[('type', '=', 'product')]")
    categ_ids = fields.Many2many('product.category', string='Categorías Contables', copy=False)

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
        if self.location_ids:
            wh += _add_where('sl', 'id', self.location_ids)

        if self.product_ids:
            wh += _add_where('sq', 'product_id', self.product_ids)

        if self.categ_ids:
            wh += _add_where('pt', 'categ_id', self.categ_ids)

            
        #add_fields_insert, add_fields_select, add_fields_from = self.extended_compute_fields()
            
        cr.execute(f'DELETE FROM report_stock_quant_line WHERE create_uid = {uid}')
            
        qry = f'''
            INSERT INTO report_stock_quant_line (product_id, product_brand_id, location_id, lot_id,
                quantity, reserved_quantity, available_qty, categ_id,
                create_date, write_date, product_uom_id)
                SELECT
                    sq.product_id, pt.product_brand_id, sq.location_id, sq.lot_id, sq.quantity, sq.reserved_quantity,
                    (sq.quantity - sq.reserved_quantity), pt.categ_id, 
                    '{dt_now}', '{dt_now}', pt.uom_id
                FROM
                    stock_quant sq
                    INNER JOIN product_product pp ON sq.product_id = pp.id
                    INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    INNER JOIN stock_location sl ON sq.location_id = sl.id
                WHERE
                    sl.usage = 'internal' AND 
                    sq.quantity > 0.0 
                    {wh}
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
        if self.location_ids:
            wh += _add_where('sl', 'id', self.location_ids)

        if self.product_ids:
            wh += _add_where('sq', 'product_id', self.product_ids)

        if self.categ_ids:
            wh += _add_where('pt', 'categ_id', self.categ_ids)
        
        excel_qry = f'''            SELECT 
                pp.default_code, pt.name, pb.name, sl.name, spl.name,  pc.name,  uu.name, 
                rsql.quantity, rsql.reserved_quantity, rsql.available_qty 
            FROM
                report_stock_quant_line rsql
                INNER JOIN product_product pp ON pp.id = rsql.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                INNER JOIN stock_location sl ON sl.id = rsql.location_id
                LEFT JOIN product_brand pb ON pb.id = rsql.product_brand_id
                LEFT JOIN stock_production_lot spl ON spl.id = rsql.lot_id
                LEFT JOIN product_category pc ON pc.id = rsql.categ_id
                LEFT JOIN uom_uom uu ON uu.id = rsql.product_uom_id
            WHERE
                sl.usage = 'internal' AND 
                rsql.quantity > 0.0 
                {wh}
        '''
        cr.execute(excel_qry)
        result = cr.fetchall()

        return result

    def get_xlsx_report(self):
        result = self._button_excel()
        output = io.BytesIO()
        titles = ['REF. PRODUCTO', 
                  'PRODUCTO', 
                  'MARCA',
                  'UBICACIÓN', 
                  'LOTE', 
                  'CATEGORÍA', 
                  'U. MEDIDA', 
                  'CANTIDAD FISICA', 
                  'CANTIDAD RESERVADA', 
                  'CANTIDAD DISPONIBLE'
                  ]
    
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()

        # Formants
        titles_format = workbook.add_format()
        titles_format.set_align("center")
        titles_format.set_bold()
        worksheet.set_column("A:J", 22)
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
        self.xls_filename = "report_stock.xlsx"

    
    def button_bi(self):
        self.compute_report()
        return_dict = {}
        if 'pivot' in self._context:
            view_id = self.env['ir.ui.view'].search([('name','=','report_stock_quant_line_pivot')], limit=1)
            return_dict.update({'view_mode': 'pivot'})
        else:
            view_id = self.env['ir.ui.view'].search([('name','=','report_stock_quant_line_pivot')], limit=1)
            search_view_id = self.env['ir.ui.view'].search([('name','=','report_stock_quant_line_search')], limit=1)
            return_dict.update({
                'search_view_id': search_view_id.id,
                'view_mode': 'tree'})
        return_dict.update({
            'name': 'Disponibilidad Stock',
            'view_type': 'pivot',
            'view_id': view_id.id,
            'res_model': 'report.stock.quant.line',
            'type': 'ir.actions.act_window',
        })
        return return_dict
    
    
class ReportStockQuantLine(models.Model):
    _name = 'report.stock.quant.line'
    _description = 'Lineas del reporte Disponibilidad Stock'
    _order = 'product_id,location_id,available_qty'
    _report_vacuum = True
    
    product_id = fields.Many2one('product.product', 'Producto', copy=False, readonly=True, required=True, index=True)
    location_id = fields.Many2one('stock.location', 'Ubicación', copy=False, readonly=True, required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lote/Serial', copy=False, readonly=True, index=True)
    quantity = fields.Float('Cantidad Física', copy=False, readonly=True, required=True,
                            digits=dp.get_precision('Product Unit of Measure'))
    reserved_quantity = fields.Float('Cantidad Reservada', digits=dp.get_precision('Product Unit of Measure'),
                                     copy=False, readonly=True, required=True)
    available_qty = fields.Float('Cantidad Disponible', digits=dp.get_precision('Product Unit of Measure'),
                                 copy=False, readonly=True, required=True)
    categ_id = fields.Many2one('product.category', 'Categoría Contable', copy=False, readonly=True, index=True)
    product_brand_id = fields.Many2one(comodel_name="product.brand", string="Marca", copy=False, readonly=True, index=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unidad de Medida', readonly=True, copy=False)
