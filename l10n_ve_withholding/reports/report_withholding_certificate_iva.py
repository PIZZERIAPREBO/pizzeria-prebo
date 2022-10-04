# coding: utf-8


import time
from datetime import datetime

from odoo import models, api, _
from odoo.exceptions import UserError, Warning, ValidationError


class CertificateIvaReport(models.AbstractModel):
    _name = 'report.l10n_ve_withholding.report_withholding_certificate_iva'
    _description = 'Certificate IVA Report'

    def _get_exempt_amount(self, invoice_id):
        exempt_amount = 0
        sql="""
        SELECT SUM(l.price_subtotal) AS exento, l.move_id AS moveid 
        FROM account_move_line AS l  
        INNER JOIN account_move_line_account_tax_rel AS r ON l.id=r.account_move_line_id  
        INNER JOIN account_tax AS t ON r.account_tax_id=t.id  
        WHERE  t.type_tax_use='purchase' AND t.amount=0 AND l.move_id=%d 
        GROUP BY l.move_id
        """%(invoice_id)
        self._cr.execute(sql)
        res = self._cr.fetchone()
        if res:
            exempt_amount = res[0]
        return exempt_amount

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            raise UserError(_("You need select a data to print."))
        data = self.env['account.payment'].browse(docids)
        #Datos de la factura del proveedor
        invoice_id = 0
        invoice_type = '01'
        invoice_date = ''
        control_number = 0
        supplier_invoice_number = ''
        supplier_refund_number = 0
        exempt_amount = 0
        invoiced_amount = 0
        withholdable_invoiced_amount = 0
        if data.withholdable_invoiced_amount:
            invoiced_amount = data.withholdable_invoiced_amount

        sql="""
        SELECT 
            m.id AS invoice,
            m.invoice_date AS invoice_date,
            m.type AS type,
            m.ref AS supplier_invoice_number,
            m.l10n_ve_document_number AS control_number
        FROM  account_tax AS t  
        INNER JOIN account_payment  AS p ON t.id=p.tax_withholding_id  
        INNER JOIN account_move_line_payment_group_to_pay_rel AS g ON p.payment_group_id=g.payment_group_id  
        INNER JOIN account_move_line AS l ON g.to_pay_line_id=l.id  
        INNER JOIN account_move AS m ON m.id=l.move_id  
        WHERE t.type_tax_use='supplier' AND t.withholding_type='partner_tax' AND p.id=%d
        """%(data.id)
        self._cr.execute(sql)
        result = self._cr.fetchone()
        if result:
            invoice_id = result[0]
            if result[1]:
                d = result[1]
                invoice_date = d.strftime("%d/%m/%Y")
            supplier_invoice_number = result[3]
            control_number = result[4]
            if result[2] == 'in_refund':
                invoice_type = '03'
                supplier_invoice_number = ''
                supplier_refund_number = result[3]
            exempt_amount = self._get_exempt_amount(invoice_id)
            withholdable_invoiced_amount = invoiced_amount - exempt_amount

        res = dict()
        return {
            'data': data,
            'invoice_type': invoice_type,
            'invoice_date': invoice_date,
            'control_number': control_number,
            'supplier_invoice_number': supplier_invoice_number,
            'exempt_amount': exempt_amount,
            'withholdable_invoiced_amount': withholdable_invoiced_amount,
            'lines': res,
        }
