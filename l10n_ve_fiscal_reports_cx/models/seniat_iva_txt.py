# coding: utf-8

import base64
import time

from odoo.addons import decimal_precision as dp
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class SeniatIvaTxt(models.Model):
    _name = 'seniat.iva.txt'
    _description = 'Generate IVA TXT'

    name = fields.Char(
        string='Description', size=128, required=True, select=True,
        default=lambda self: 'Withholding Vat ' + time.strftime('%m/%Y'),
        help="Description about statement of withholding income")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        states={'draft': [('readonly', False)]}, help='Company',
        default=lambda self: self.env['res.company']._company_default_get())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='State', select=True, readonly=True, default='draft',
        help="proof status")
    period = fields.Date(string='Period')
    date_start = fields.Date(
        string='Begin Date', required=True,
        states={'draft': [('readonly', False)]},
        help="Begin date of period")
    date_end = fields.Date(
        string='End date', required=True,
        states={'draft': [('readonly', False)]},
        help="End date of period")
    total_withheld = fields.Float(
        string='Total withheld',
        store=True,help="Total withheld")
    total_base = fields.Float(
        string='Total taxable',
        store=True, help="Total Taxable Base")
    txt_name = fields.Char('File name')
    txt_file = fields.Binary('Descargar TXT', states={'done': [('invisible', False)]} )

    @api.model
    def name_get(self):
        """ Return a list with id and name of the current register
        """
        res = [(r.id, r.name) for r in self]
        return res

    def action_anular(self):
        """ Return document state to draft
        """
        self.write({'state': 'draft'})
        return True

    @api.model
    def get_type_document(self, type):
        """ Return the document type
        @param type: line of the current document
        """
        inv_type = '03'
        if type == 'in_invoice':
            inv_type = '01'

        return inv_type

    @api.model
    def generate_txt(self):
        """ Return string with data of the current document
        """
        result = {}
        alicuota  = 0
        total_base = 0
        total_withheld = 0 
        txt_string = ''
        vat_company = self.company_id.partner_id.vat
        operation_type = 'C'

        #Invoices for the period
        sql = """
        SELECT  m.id,m.invoice_date, p.vat,m.ref,m.l10n_ve_document_number,p.vat_retention,m.type,
        COALESCE(ce.exento,0) AS exento,
        COALESCE(tx.percent_amount,0) AS percent, 
        COALESCE(tx.base_amount,0) AS base, 
        COALESCE(rt.amount_ret,0) AS amount,
        rt.number_ret,
        fc.document_ref,
        p.id
        FROM    account_move AS m
        INNER JOIN res_partner AS p ON m.partner_id=p.id
        FULL OUTER JOIN (
            SELECT SUM(l.price_subtotal) AS exento, l.move_id AS moveid
            FROM account_move_line AS l 
            INNER JOIN account_move_line_account_tax_rel AS r ON l.id=r.account_move_line_id 
            INNER JOIN account_tax AS t ON r.account_tax_id=t.id 
            WHERE  t.type_tax_use='purchase' AND t.amount=0
            GROUP BY l.move_id
        ) AS ce ON m.id=ce.moveid
        FULL OUTER JOIN (
            SELECT t.amount AS percent_amount,l.tax_base_amount AS base_amount,l.move_id AS invoice 
            FROM  account_tax AS t 
            INNER JOIN account_move_line AS l ON t.id=l.tax_line_id 
            WHERE t.type_tax_use='purchase'
        ) AS tx ON m.id=tx.invoice
        FULL OUTER JOIN (
            SELECT p.withholding_number AS number_ret,p.amount AS amount_ret,l.move_id AS invoice 
            FROM  account_tax AS t 
            INNER JOIN account_payment  AS p ON t.id=p.tax_withholding_id 
            INNER JOIN account_move_line_payment_group_to_pay_rel AS g ON p.payment_group_id=g.payment_group_id 
            INNER JOIN account_move_line AS l ON g.to_pay_line_id=l.id 
            WHERE t.type_tax_use='supplier' AND t.withholding_type='partner_tax'
        ) AS rt ON m.id=rt.invoice
        FULL OUTER JOIN (
            SELECT mv.ref AS document_ref, mv.id AS moveid 
            FROM  account_move AS mv
        ) AS fc ON m.reversed_entry_id=fc.moveid
        WHERE m.state not in ('cancel','draft') 
        AND m.type in ('in_invoice','in_refund') 
        AND m.invoice_date BETWEEN '%s' AND '%s'  
        ORDER BY m.name ;""" %(str(self.date_start),str(self.date_end)) 

        self._cr.execute(sql)
        rows = self._cr.fetchall()
        for row in rows:
            date_start = str(self.date_start)
            period = date_start[:4]+date_start[5:7]
            invoice_date = row[1]
            document_type = self.get_type_document(row[6])
            invoice_number = '0'
            if row[3]:
                invoice_number = row[3]
            document_number = '0'
            if row[4]:
                document_number = row[4]
            amount_exempt = row[7]
            alicuota = row[8]
            untaxed = row[9]
            amount_withheld = row[10]
            amount_total = amount_exempt + untaxed + amount_withheld
            voucher_number = row[11]
            document_affected = '0'
            if row[12]:
                document_affected = row[12]
            partner_id = row[13]
            partner = self.env['res.partner'].browse(partner_id)
            vat_partner= partner.l10n_latam_identification_type_id.l10n_ve_code+partner.vat
            total_base += untaxed
            total_withheld += amount_withheld

            txt_string = (
                txt_string + vat_company + '\t' + str(period) + '\t'
                +str(invoice_date) + '\t' + operation_type +
                '\t' + document_type + '\t' + vat_partner + '\t' +
                invoice_number + '\t' + document_number+ '\t' +
                str(round(amount_total, 2)) + '\t' +
                str(round(untaxed, 2)) + '\t' +
                str(round(amount_withheld, 2)) + '\t' +
                document_affected + '\t' + voucher_number + '\t' +
                str(round(amount_exempt, 2)) + '\t' + str(alicuota) +
                '\t' + '0' + '\n')
        result = {'data_txt':txt_string,'total_base':total_base,'total_withheld':total_withheld}
        return result

    @api.model
    def _write_attachment(self, data):
        """ Encrypt txt, save it to the db
        @param data: location to save document
        """
        fecha = time.strftime('%Y_%m_%d_%H%M%S')
        name = 'IVA_' + fecha + '.' + 'txt'

        data_file = data.get('data_txt', None)
        total_base = data.get('total_base', 0)
        total_withheld = data.get('total_withheld', 0)
        txt_name = name
        txt_file = data_file.encode('utf-8')
        txt_file = base64.encodestring(txt_file)
        self.write({'txt_name': txt_name, 'txt_file': txt_file,'total_withheld':total_withheld,'total_base':total_base})

    def action_generate_txt(self):
        """ 
        """
        data = self.generate_txt()
        self._write_attachment(data)

        return True

    def action_done(self):
        """ Transfer the document status to done
        """
        self.write({'state': 'done'})

        return True
