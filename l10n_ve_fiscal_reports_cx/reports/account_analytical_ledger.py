# coding: utf-8

import time
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning, ValidationError


class AnalyticalLedgerReport(models.AbstractModel):
    _name = 'report.l10n_ve_fiscal_reports_cx.template_analytical_ledger'
    _description = 'Analytical Ledger Report'

    totalg_debit = 0
    totalg_credit = 0
    saldo = 0

    def _get_account_ids(self, date_from, date_to,account_from=None,account_to=None):
        account_ids = []
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        company = self.env.user.company_id
        account_filter = ''
        if account_from and not account_to:
            account_filter =" and code='%s'"%account_from
        if not account_from and account_to:
            account_filter = " and code='%s'"%account_to
        if account_from and account_to:
            account_filter = " and code>='%s' and code<='%s'"%(account_from,account_to)
        #sql="""
        #SELECT a.id
        #FROM  account_move_line AS l
        #INNER JOIN account_account AS a ON l.account_id=a.id
        #WHERE l.parent_state='posted' and l.company_id=%d and l.date>='%s' and l.date<='%s' %s
        #GROUP BY a.id
        #ORDER BY a.code
        #"""
        sql="""
        SELECT id
        FROM  account_account
        WHERE company_id=%d %s
        ORDER BY code
        """%(int(company.id),account_filter)
        self._cr.execute(sql)
        results = self._cr.fetchall()
        if results:
            for res in results:
                account_ids.append(res[0])

        return account_ids

    def _get_accounts(self, date_from, date_to,account_from=None,account_to=None):
        self.totalg_debit = 0
        self.totalg_credit = 0
        self.saldo = 0
        results = []
        company = self.env.user.company_id
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        account_filter = ''
        account_ids = self._get_account_ids(date_from, date_to, account_from, account_to)
        if account_ids:
            account_filter = ','.join(map(str,account_ids))
        sql="""
        SELECT a.id, a.code, a.name,
        COALESCE(ml.saldo,0) AS total
        FROM  account_account AS a
        LEFT JOIN ( SELECT l.account_id as lineid,
                    COALESCE((SUM(l.debit) - SUM(l.credit)),0) AS saldo
                    FROM account_move_line AS l 
                    WHERE l.parent_state='posted' and l.company_id=%d and l.date<'%s'
                    GROUP BY l.account_id
                   ) AS ml ON ml.lineid=a.id
        WHERE a.id in (%s)
        ORDER BY a.code
        """%(int(company.id),start_date,account_filter)
        self._cr.execute(sql)
        results = self._cr.fetchall()
        return results

    def _get_account_move_lines(self, date_from, date_to,account_from=None,account_to=None):
        self.totalg_debit = 0
        self.totalg_credit = 0
        self.saldo = 0
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        company = self.env.user.company_id
        domain = [
            ('date', '>=', start_date),
            ('date', '<=', close_date),
            ('company_id', '=', int(company.id)),
            ('parent_state', '=', 'posted'),
        ]
        if account_from and not account_to:
            domain.append(('account_id','=',account_from))
        if not account_from and account_to:
            domain.append(('account_id','=',account_to))
        if account_from and account_to:
            account_ids = self._get_account_ids(date_from, date_to, account_from, account_to)
            if account_ids:
                domain.append(('account_id','in',account_ids))
        moves = self.env['account.move.line'].search(domain, order='date')
        return moves

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = self.format_date(data['form']['date_from'])
        date_to = self.format_date(data['form']['date_to'])
        account_id_from = data['form']['account_from'] 
        account_id_to = data['form']['account_to']
        today = datetime.now()
        company = self.env.user.company_id
        company_name = ''
        company_vat = ''
        if company and company.name:
            company_name = company.name
            if company.partner_id and company.partner_id.vat:
                company_vat = company.partner_id.vat

        return {
            'data': data,
            'company_name': company_name,
            'company_vat': company_vat,
            'date_from': date_from,
            'date_to': date_to,
            'today': today,
            'acounts': self._get_accounts(data['form']['date_from'],data['form']['date_to'],account_id_from,account_id_to),
            'move_lines': self._get_account_move_lines(data['form']['date_from'],data['form']['date_to'],account_id_from,account_id_to),
            'total_debit': self.totalg_debit,
            'total_credit': self.totalg_credit,
            'saldo': self.saldo,
        }

    def format_date(self, date):
        date_parts = date.split('-')
        return f'{date_parts[2]}/{date_parts[1]}/{date_parts[0]}'
