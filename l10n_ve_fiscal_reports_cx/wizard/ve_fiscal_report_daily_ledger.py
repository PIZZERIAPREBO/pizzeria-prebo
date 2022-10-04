# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class DailyLedger(models.TransientModel):
    _name = 've.fiscal.report.daily.ledger'
    _description = 'Daily Ledger Report'

    start_from_date = fields.Date(string="Fecha de Inicio", default=date(datetime.today().year, datetime.today().month, 1))
    close_from_date = fields.Date(string="Fecha de Cierre", default=datetime.today().date())

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_from': self.start_from_date,
                'date_to': self.close_from_date,
                'company_id': self.env.user.company_id,
            }
        }
        return self.env.ref('l10n_ve_fiscal_reports_cx.ve_daily_ledger_report').report_action(self, data=data)