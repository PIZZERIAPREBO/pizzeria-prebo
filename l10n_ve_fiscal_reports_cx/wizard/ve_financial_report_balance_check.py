# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo import api, fields, models
from odoo.tools.misc import get_lang
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class BalanceCheck(models.TransientModel):
    _inherit = "account.common.journal.report"
    _name = 've.financial.report.balance.check'
    _description = 'Balance Check Report'

    start_from_date = fields.Date(string="Fecha de Inicio", required=True,
                                default=date(datetime.today().year, datetime.today().month, 1))
    close_from_date = fields.Date(string="Fecha de Cierre", required=True,
                                default=datetime.today().date())
    display_account = fields.Selection([('all', 'All'),
                                        ('not_zero', 'With balance is not equal to 0'), ],
                                        string='Cuentas', default='all')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env['res.company']._company_default_get())

    def report_pdf(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data, pdf=True)

    def _print_report(self, data=None, pdf=False):

        data = {
            'start_from_date': self.start_from_date,
            'close_from_date': self.close_from_date,
            'company_id': self.company_id.id,
            'display_account': self.display_account,
        }

        if pdf:   
            return self.env.ref('l10n_ve_fiscal_reports_cx.action_report_balance_check').report_action(self, data=data)
        else:
            return 

