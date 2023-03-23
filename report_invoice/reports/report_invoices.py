# -*- coding: utf-8 -*-


from odoo import fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import base64
import datetime
import xlsxwriter
from io import BytesIO
import io


class ReportInvoice(models.TransientModel):
    _name = "report.invoice"
    
    name = fields.Char('Nombre', default='Informe de Facturados', readonly=True)
    date_from = fields.Date('Desde', required=True, default=(fields.Datetime.now() - relativedelta(month=1)))
    date_to = fields.Date('Hasta', required=True, default=(fields.Datetime.now()).date())
    partner_ids = fields.Many2many('res.partner', string='Clientes') 
    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    

    def analysis(self):
        view_id = self.env['ir.ui.view'].search([('name','=','account.view_account_invoice_report_pivot')])
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        domain = [('invoice_date', '>', dt_from), ('invoice_date', '<=', dt_to)]
        return {
                'domain': domain,
                'name': 'Análisis de Facturados',
                'view_type': 'form',
                'view_mode': 'pivot',
                'view_id': view_id.id, 
                'res_model': 'account.invoice.report',
                'type': 'ir.actions.act_window'
            }
    
    def _compute_excel(self):
        def _add_wh(fld, tbl):
            return " AND {} IN ({})".format(fld, ','.join(str(x.id) for x in tbl))
    
        #APLICAR FILTROS
        wh = '' 
        if self.partner_ids:
            wh = _add_wh('am.partner_id', self.partner_ids)
        cr = self.env.cr
        dt_from = str(self.date_from)
        dt_to = str(self.date_to)
        cr.execute(f'''SELECT
                            am.invoice_date, 
                            am.name, 
                            aa.name,
                            pt.name,
                            pc.name,
                            pb.name,
                            uu.name,
                            aml.quantity,
                            aml.price_subtotal,
                            rp.vat,
                            rp.name,
                            rp2.name,
                            cm.name
                            

                        FROM account_move am
                            INNER JOIN account_move_line aml ON am.id = aml.move_id
                            INNER JOIN account_analytic_account aa ON aml.analytic_account_id = aa.id
                            INNER JOIN product_product pp ON aml.product_id = pp.id
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            INNER JOIN product_category pc ON pt.categ_id = pc.id
                            INNER JOIN product_brand pb ON pt.product_brand_id = pb.id
                            INNER JOIN uom_uom uu ON pt.uom_id = uu.id                          
                            INNER JOIN res_partner rp ON am.partner_id = rp.id
                            INNER JOIN res_users ru ON am.invoice_user_id = ru.id
                            INNER JOIN res_partner rp2 ON ru.partner_id = rp2.id
                            INNER JOIN crm_team cm ON am.team_id = cm.id 
                             

                        WHERE
                            am.move_type IN ('out_invoice', 'out_refund','out_receipt') AND
                            am.invoice_date BETWEEN   '{dt_from}' AND '{dt_to}' {wh}
                        
                        GROUP BY
                        am.name,
                        pc.name,
                        pt.name,
                        am.invoice_date,
                        aa.name,
                        pb.name,
                        uu.name,
                        aml.quantity,
                        aml.price_subtotal,
                        rp.vat,
                        rp.name,
                        rp2.name,
                        cm.name
                    
                      ''')
        result = cr.fetchall()
        return result
        
    def get_xlsx_report(self):
        result = self._compute_excel()
        output = io.BytesIO()
        titles = [
                'Fecha', 
                'Factura', 
                'Cuenta', 
                'Producto', 
                'Categoria',
                'Marca',
                'Unidad de medida', 
                'Cantidad', 
                'Valor', 
                'Nit', 
                'Cliente',
                'Vendedor',
                'Equipo de ventas'
                ]
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()

        # Formants
        titles_format = workbook.add_format()
        titles_format.set_align("center")
        titles_format.set_bold()
        worksheet.set_column("A:M", 22)
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


