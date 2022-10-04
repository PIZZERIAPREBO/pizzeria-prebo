# coding: utf-8


import time
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning, ValidationError


class DailyLedgerReport(models.AbstractModel):
    _name = 'report.l10n_ve_fiscal_reports_cx.template_daily_ledger'
    _description = 'Daily Ledger Report'

    total_debit = 0
    total_credit = 0

    def _get_account_move_lines(self, date_from, date_to):
        self.total_debit = 0
        self.total_credit = 0
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        company = self.env.user.company_id
        sql="""
        SELECT a.code,a.name,
        COALESCE(SUM(l.debit),0) AS total_debit,
        COALESCE(SUM(l.credit),0) AS total_credit
        FROM  account_move_line AS l
        INNER JOIN account_account AS a ON l.account_id=a.id
        WHERE l.parent_state='posted' and l.company_id=%d and l.date>='%s' and l.date<='%s' 
        GROUP BY a.code,a.name
        ORDER BY a.code
        """%(int(company.id),start_date,close_date)
        self._cr.execute(sql)
        results = self._cr.fetchall()
        if results:
            for res in results:
                if res[2]:
                    self.total_debit += res[2]
                if res[3]:
                    self.total_credit += res[3]
        return results

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = self.format_date(data['form']['date_from'])
        date_to = self.format_date(data['form']['date_to'])
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
            'lines': self._get_account_move_lines(data['form']['date_from'],data['form']['date_to']),
            'total_debit': self.total_debit,
            'total_credit': self.total_credit,
        }

    def format_date(self, date):
        date_parts = date.split('-')
        return f'{date_parts[2]}/{date_parts[1]}/{date_parts[0]}'

#<record id="paperformat_custom" model="report.paperformat">
#<field name="name">Custom format</field>
#<field name="default" eval="True" />
#<field name="format">custom</field>
#<field name="page_height">90</field>
#<field name="page_width">180</field>
#<field name="orientation">Portrait</field>
#<field name="margin_top">30</field>
#<field name="margin_bottom">30</field>
#<field name="margin_left">10</field>
#<field name="margin_right">10</field>
#<field name="header_line" eval="False" />
#<field name="header_spacing">20</field>
#<field name="dpi">100</field>
#</record>
