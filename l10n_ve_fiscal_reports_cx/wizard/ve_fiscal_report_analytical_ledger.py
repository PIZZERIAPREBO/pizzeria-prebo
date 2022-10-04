# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class AnalyticalLedger(models.TransientModel):
    _name = 've.fiscal.report.analytical.ledger'
    _description = 'Analy Ledger Report'

    start_from_date = fields.Date(string="Fecha de Inicio", default=date(datetime.today().year, datetime.today().month, 1))
    close_from_date = fields.Date(string="Fecha de Cierre", default=datetime.today().date())
    account_from = fields.Many2one('account.account', string='Account From', check_company=True,
                                    domain=[('deprecated', '=', False)])
    account_to = fields.Many2one('account.account', string='Account From', check_company=True,
                                    domain=[('deprecated', '=', False)])

    def get_report(self):
        account_from = None
        account_to = None
        if self.account_from:
            account_from = self.account_from.code
        if self.account_from:
            account_to = self.account_to.code
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_from': self.start_from_date,
                'date_to': self.close_from_date,
                'account_from': account_from,
                'account_to': account_to,
            }
        }
        return self.env.ref('l10n_ve_fiscal_reports_cx.ve_analytical_ledger_report').report_action(self, data=data)