# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    withholding_target = fields.Selection([
        ("value", "I.V.A"),
        ("income", "I.S.L.R"),
        ], string="Impuesto a Retener", default= None)

    is_payment_methods_selected = fields.Boolean(compute='_eval_selected_payment_methods', default=False)


    @api.depends('inbound_payment_method_ids', 'outbound_payment_method_ids')
    def _eval_selected_payment_methods(self):
        inbound_methods  = [method.code for method in self.inbound_payment_method_ids]
        outbound_methods = [method.code for method in self.outbound_payment_method_ids]

        for rec in self:

            rec.is_payment_methods_selected = 'withholding' in inbound_methods \
                or 'withholding' in outbound_methods