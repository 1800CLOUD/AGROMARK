# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
import datetime
import xlsxwriter
from io import BytesIO
import io


class ReportInvoice(models.TransientModel):
    _name = "report.invoice"
    _description = 'Reporte de productos facturados'


    name = fields.Char('Nombre', default='Informe de Facturados', readonly=True)
    date_from = fields.Date('Desde', required=True, default=(fields.Date.today() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Date.today()))
    partner_ids = fields.Many2many('res.partner', string='Clientes') 
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
        if self.partner_ids:
            wh += _add_where('rp', 'partner_id', self.partner_ids)


            
        #add_fields_insert, add_fields_select, add_fields_from = self.extended_compute_fields()
            
        cr.execute(f'DELETE FROM invoice_report_line')
            
        qry = f'''
            INSERT INTO invoice_report_line (invoice_date, sale_id, move_id, analytic_account_id, product_id, default_code, categ_id, product_brand_id, product_uom_id, 
                quantity, price_subtotal,partner_vat, partner_id, city_partner_id, invoice_user_id, move_type, product_type, create_date, write_date)
                SELECT
            
                    am.invoice_date, 
                    so.id,
                    am.id,
                    aml.analytic_account_id, 
                    aml.product_id,
                    pt.default_code,
                    pt.categ_id,
                    pt.product_brand_id,
                    pt.uom_id,
                    CASE 
                        WHEN am.move_type = 'out_refund' THEN aml.quantity * (-1)
                        ELSE aml.quantity 
                    END,
                    CASE
                        WHEN am.move_type = 'out_invoice' THEN aml.balance * (-1)
                        ELSE aml.balance * (-1) 
                    END,
                    rp.vat,
                    am.partner_id,
                    rp.city_id,
                    am.invoice_user_id,
                    am.move_type,
                    pt.detailed_type,
                    '{dt_now}', 
                    '{dt_now}'

                FROM account_move_line aml
                    LEFT JOIN account_move am ON aml.move_id = am.id
                    LEFT JOIN sale_order so ON am.sale_id = so.id
                    INNER JOIN product_product pp ON aml.product_id = pp.id
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN account_analytic_account aa ON aml.analytic_account_id = aa.id
                    LEFT JOIN product_category pc ON pt.categ_id = pc.id
                    LEFT JOIN uom_uom uu ON pt.uom_id = uu.id                          
                    LEFT JOIN res_partner rp ON so.partner_id = rp.id
                    LEFT JOIN res_users ru ON so.user_id = ru.id
                    LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.id
                    LEFT JOIN product_brand pb ON pt.product_brand_id = pb.id
                    LEFT JOIN res_city rc ON am.city_id = rc.id 
        

                 WHERE
                    pt.detailed_type IN ('product','service') AND
                    am.move_type IN ('out_invoice', 'out_refund') AND
                    am.state = 'posted' AND
                    am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' {wh}
                        
                GROUP BY
                    am.invoice_date,
                    so.id,
                    am.id,
                    aml.analytic_account_id, 
                    aml.product_id,
                    pt.default_code,
                    pt.categ_id,
                    pt.product_brand_id,
                    pt.uom_id,
                    rp.vat,
                    am.partner_id,
                    rp.city_id,
                    am.invoice_user_id,
                    am.move_type,
                    aml.quantity,
                    aml.balance,
                    pt.detailed_type,
                    aml.id
        '''
        cr.execute(qry)

    def analysis(self):
        self.compute_report()
        view_id = self.env['ir.ui.view'].search([('name','=','report_invoice.view_account_invoice_report_line_pivot')])
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        domain = [('invoice_date', '>', dt_from), ('invoice_date', '<=', dt_to)]
        return {
                'domain': domain,
                'name': 'Análisis de Facturados',
                'view_type': 'form',
                'view_mode': 'pivot',
                'view_id': view_id.id, 
                'res_model': 'invoice.report.line',
                'type': 'ir.actions.act_window'
            }
    
    def _compute_excel(self):
        def _add_wh(fld, tbl):
            return " AND {} IN ({})".format(fld, ','.join(str(x.id) for x in tbl))
    
        #APLICAR FILTROS
        wh = '' 
        if self.partner_ids:
            wh = _add_wh('so.partner_id', self.partner_ids)
        cr = self.env.cr
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        cr.execute(f'''SELECT
                            am.invoice_date, 
                            so.name,
                            am.name, 
                            aa.name,
                            pt.default_code,
                            pt.name,
                            pc.name,
                            pb.name,
                            uu.name,
                            CASE 
                                WHEN am.move_type = 'out_refund' THEN aml.quantity * (-1)
                                ELSE aml.quantity 
                            END AS total_quantity,
                            CASE
                                WHEN am.move_type = 'out_invoice' THEN aml.balance * (-1)
                                ELSE aml.balance * (-1) 
                            END AS total_price_subtotal,
                            rp.vat,
                            rp.name,
                            rc2.name,
                            rc.name,
                            rp2.name,
                            cm.name

                        FROM account_move_line aml
                            LEFT JOIN account_move am ON aml.move_id = am.id
                            LEFT JOIN sale_order so ON am.sale_id = so.id
                            LEFT JOIN product_product pp ON aml.product_id = pp.id
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN sale_order_line sol ON so.id = sol.order_id AND sol.product_id = pp.id 
                            LEFT JOIN account_analytic_account aa ON aml.analytic_account_id = aa.id
                            LEFT JOIN product_category pc ON pt.categ_id = pc.id
                            LEFT JOIN uom_uom uu ON pt.uom_id = uu.id                          
                            LEFT JOIN res_partner rp ON so.partner_id = rp.id
                            LEFT JOIN res_users ru ON so.user_id = ru.id
                            LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.id
                            LEFT JOIN crm_team cm ON so.team_id = cm.id 
                            LEFT JOIN product_brand pb ON pt.product_brand_id = pb.id
                            LEFT JOIN res_city rc ON am.city_id = rc.id 
                            LEFT JOIN res_city rc2 ON rp.city_id = rc2.id
                             

                        WHERE
                            pt.detailed_type IN ('product', 'service')
                            am.move_type IN ('out_invoice', 'out_refund') AND
                            am.state = 'posted' AND
                            am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' {wh}
                        
                        GROUP BY
                        am.invoice_date,
                        so.name,
                        am.name,
                        pt.default_code,
                        pt.name,
                        pc.name,
                        aa.name,
                        pb.name,
                        uu.name,
                        rp.vat,
                        rp.name,
                        rc2.name,
                        rc.name,
                        rp2.name,
                        cm.name,
                        am.move_type,
                        aml.quantity,
                        aml.balance,
                        aml.id
                        
                    
                      ''')
        result = cr.fetchall()
        return result
        
    def get_xlsx_report(self):
        result = self._compute_excel()
        output = io.BytesIO()
        titles = [
                'Fecha', 
                'Orden de venta', 
                '# Factura',
                'Cuenta analítica', 
                'Referencia Interna',
                'Producto',
                'Categoria',
                'Marca',
                'Unidad de medida', 
                'Cantidad', 
                'Valor', 
                'Nit', 
                'Cliente',
                'Ciudad Cliente',
                'Ciudad Factura',
                'Vendedor',
                'Equipo de ventas'
                ]
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()

        # Formants
        titles_format = workbook.add_format()
        titles_format.set_align("center")
        titles_format.set_bold()
        worksheet.set_column("A:Q", 22)
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


class InvoiceReportLine(models.TransientModel):
    _name = "invoice.report.line"
    _description = "Lineas de reporte de Facturados"
    

    # ==== Invoice fields ====
    move_id = fields.Many2one('account.move', copy=False, readonly=True, required=True)
    sale_id = fields.Many2one('sale.order', string='Orden de Venta', readonly=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='cliente', readonly=True, copy=False)
    invoice_user_id = fields.Many2one('res.users', string='Vendedor', readonly=True, copy=False)
    move_type = fields.Selection([
        ('out_invoice', 'Factura Cliente'),
        ('out_refund', 'Factura rectificativa'),
        ], string='Tipo de Factura', readonly=True)
    invoice_date = fields.Date(readonly=True, string="Fecha de Factura", copy=False)

    # ==== Invoice line fields ====
    quantity = fields.Float(string='Cantidad Facturada', readonly=True, index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True, required=True, copy=False, index=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', readonly=True)
    categ_id = fields.Many2one('product.category', string='Categoria Producto', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta analítica', copy=False)
    price_subtotal = fields.Float(string='V. antes Impuesto', readonly=True, required=True, index=True, copy=False )
    partner_vat = fields.Char('NIT', readonly=True, index=True, copy=False)
    default_code = fields.Char('Referencia interna', copy=False, readonly=True, index=True)
    city_partner_id = fields.Many2one('res.city', string="Ciudad Cliente", readonly=True, copy=False)
    product_brand_id = fields.Many2one(comodel_name="product.brand", string="Marca", copy=False, readonly=True, index=True)
    product_type = fields.Selection([
        ('product', 'Almacenable'),
        ('service', 'Servicio'),
        ('consu', 'Consumible'),
        ], string='Tipo de producto', readonly=True)
    

