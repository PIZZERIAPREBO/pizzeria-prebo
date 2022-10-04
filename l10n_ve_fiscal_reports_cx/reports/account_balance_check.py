# coding: utf-8


import time
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning, ValidationError


class BalanceCheckReport(models.AbstractModel):
    _name = 'report.l10n_ve_fiscal_reports_cx.financial_balance_check'
    _description = 'alance Check Report'

    total_debit = 0
    total_credit = 0
    ttbc = 0
    ttcc = 0
    ttac = 0
    ttanc = 0
    ttpg = 0
    ttaf = 0

    def _get_move_lines(self, date_from, date_to,internal_type,company_id,display='all'):
        self.total_debit = 0
        self.total_credit = 0
        results = []
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        if display == 'all':
            sql="""
            SELECT ac.codigo,
                   ac.cuenta,
                   SUM(ac.inicial) AS anterior,
                   SUM(ac.debe) AS debito,
                   SUM(ac.haber) AS credito,
                   SUM(ac.inicial) + SUM(ac.debe) - SUM(ac.haber) AS saldo
            FROM (
                    (SELECT a1.code AS codigo,a1.name AS cuenta,
                    COALESCE(ml1.inicial,0) AS inicial,
                    0 AS debe, 0 AS haber 
                    FROM account_account AS a1 
                    LEFT JOIN (
                                SELECT l1.account_id as lineid,
                                COALESCE((SUM(l1.debit) - SUM(l1.credit)),0) AS inicial
                                FROM account_move_line AS l1
                                WHERE l1.company_id=%d AND l1.parent_state='posted' AND l1.date < '%s' 
                                GROUP BY l1.account_id
                               ) AS ml1 ON a1.id=ml1.lineid
                    WHERE a1.user_type_id=%d AND a1.company_id=%d
                    ORDER BY a1.code)
                    UNION ALL
                    (SELECT a2.code AS codigo,a2.name AS cuenta, 0 as inicial,
                    COALESCE(ml2.debit,0) AS debe, 
                    COALESCE(ml2.credit,0) AS haber 
                    FROM account_account AS a2 
                    LEFT JOIN (
                                SELECT l2.account_id as lineid,
                                COALESCE(SUM(l2.debit),0) AS debit, 
                                COALESCE(SUM(l2.credit),0) AS credit 
                                FROM account_move_line AS l2
                                WHERE l2.parent_state='posted' AND l2.company_id=%d  AND l2.date >= '%s' AND l2.date <= '%s'
                    GROUP BY l2.account_id) AS ml2 ON a2.id=ml2.lineid
                    WHERE a2.user_type_id=%d AND a2.company_id=%d
                    ORDER BY a2.code)
                 ) AS ac
            GROUP BY ac.codigo, ac.cuenta
            ORDER BY ac.Codigo
            """%(company_id,start_date,internal_type,company_id,company_id,start_date,close_date,internal_type,company_id)
        else:
            sql="""
            SELECT ac.codigo,
                   ac.cuenta,
                   COALESCE(SUM(ac.inicial),0) AS anterior,
                   COALESCE(SUM(ac.debe),0) AS debito,
                   COALESCE(SUM(ac.haber),0) AS credito,
                   COALESCE(SUM(ac.inicial),0) + SUM(ac.debe) - SUM(ac.haber) AS saldo
            FROM (
                    (SELECT a1.code AS codigo,a1.name AS cuenta,
                    SUM(l1.debit - l1.credit) as inicial,
                    0 AS debe, 0 AS haber 
                    FROM account_account AS a1 
                    INNER JOIN account_move_line AS l1 ON a1.id=l1.account_id
                    WHERE a1.user_type_id=%d 
                    AND l1.company_id=%d AND l1.parent_state='posted' AND l1.date < '%s' 
                    GROUP BY a1.code,a1.name
                    ORDER BY a1.code)
                    UNION ALL
                    (SELECT a2.code AS codigo,a2.name AS cuenta,
                    0 as inicial,
                    SUM(l2.debit) AS debe, 
                    SUM(l2.credit) AS haber 
                    FROM account_account AS a2 
                    INNER JOIN account_move_line AS l2 ON a2.id=l2.account_id
                    WHERE a2.user_type_id=%d
                    AND l2.parent_state='posted' 
                    AND l2.company_id=%d  AND l2.date >= '%s' AND l2.date <= '%s'
                    GROUP BY a2.code,a2.name
                    ORDER BY a2.code)
                 ) AS ac
            GROUP BY ac.codigo, ac.cuenta
            ORDER BY ac.Codigo
            """%(internal_type,company_id,start_date,internal_type,company_id,start_date,close_date)
        self._cr.execute(sql)
        results = self._cr.fetchall()
        return results

    def _get_assets(self, date_from, date_to,internal_type):
        results = []
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        close_date = datetime.strptime(date_to, '%Y-%m-%d')
        company = self.env.user.company_id
        sql="""
        SELECT ac.codigo,
               ac.cuenta,
               COALESCE(SUM(ac.inicial),0) AS anterior,
               COALESCE(SUM(ac.debe),0) AS debito,
               COALESCE(SUM(ac.haber),0) AS credito,
               COALESCE(SUM(ac.inicial),0) + SUM(ac.debe) - SUM(ac.haber) AS saldo
        FROM (
                (SELECT a1.code AS codigo,a1.name AS cuenta,
                SUM(l1.debit - l1.credit) as inicial,
                0 AS debe, 0 AS haber 
                FROM account_account AS a1 
                INNER JOIN account_move_line AS l1 ON a1.id=l1.account_id
                WHERE a1.user_type_id=%d 
                AND l1.company_id=%d AND l1.parent_state='posted' AND l1.date < '%s' 
                GROUP BY a1.code,a1.name
                ORDER BY a1.code)
                UNION ALL
                (SELECT a2.code AS codigo,a2.name AS cuenta,
                0 as inicial,
                SUM(l2.debit) AS debe, 
                SUM(l2.credit) AS haber 
                FROM account_account AS a2 
                INNER JOIN account_move_line AS l2 ON a2.id=l2.account_id
                WHERE a2.user_type_id=%d
                AND l2.parent_state='posted' 
                AND l2.company_id=%d  AND l2.date >= '%s' AND l2.date <= '%s'
                GROUP BY a2.code,a2.name
                ORDER BY a2.code)
             ) AS ac
        GROUP BY ac.codigo, ac.cuenta
        ORDER BY ac.Codigo
        """%(internal_type,int(company.id),start_date,internal_type,int(company.id),start_date,close_date)
        self._cr.execute(sql)
        results = self._cr.fetchall()
        if results:
            if internal_type == 1:
                self.ttcc = 1
            if internal_type == 3:
                self.ttbc = 3
            if internal_type == 5:
                self.ttac = 5
            if internal_type == 6:
                self.ttanc = 6
            if internal_type == 8:
                self.ttaf = 8
        return results


    @api.model
    def _get_report_values(self, docids, data=None):
        #self.ttbc = 0
        #self.ttcc = 0
        #self.ttac = 0
        #self.ttanc = 0
        #self.ttaf = 0
        #self.ttpg = 0
        date_from = self.format_date(data['start_from_date'])
        date_to = self.format_date(data['close_from_date'])
        display_account = data['display_account']
        today = datetime.now()
        company_id = data['company_id']
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
            'asset_liquidity_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],3,company_id,display_account),       #Caja y Bancos
            'asset_receivable_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],1,company_id,display_account),      #Cuestas por Cobrar
            'asset_current_assets_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],5,company_id,display_account),                 #Activos cisculantes
            'asset_nocurrent_assets_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],6,company_id,display_account),               #Activos no cisculantes
            'asset_fixed_assets_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],8,company_id,display_account),                   #Activos Fijos
            'liability_current_liabilities_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],9,company_id,display_account),    #Pasivo circulante
            'liability_payable_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],2,company_id,display_account),                #Cuestas por Pagar
            'liability_nocurrent_liabilities_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],10,company_id,display_account), #Pasivo no circulante
            'equity_equity_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],11,company_id,display_account),                   #Capital
            'income_income_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],13,company_id,display_account),                   #Ingresos
            'income_other_income_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],14,company_id,display_account),             #Otros Ingresos
            'expense_expense_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],15,company_id,display_account),                 #Gastos
            'expense_depreciation_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],16,company_id,display_account),            #Depreciaciones
            'expense_cost_revenue_lines': self._get_move_lines(data['start_from_date'],data['close_from_date'],17,company_id,display_account),            #Costos Ventas
            'total_debit': self.total_debit,
            'ttcc': self.ttcc,
            'ttbc': self.ttbc,
            'ttac': self.ttac,
            'ttanc': self.ttanc,
            'ttaf': self.ttaf,
        }

    def format_date(self, date):
        date_parts = date.split('-')
        return f'{date_parts[2]}/{date_parts[1]}/{date_parts[0]}'
