from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_withholding_islr_state = fields.Selection(
        selection=[
            ('not_apply', 'Not Apply'),
            ('not_held', 'Not Held'),
            ('in_progress', 'In Progress'),
            ('held', 'Held')
        ],
        string='Withheld',
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute='_compute_withheld_state'
    )
    xml_line_ids = fields.One2many(
        'seniat.islr.xml.line',
        'move_id',
        string='XML Items',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )


    def _prepare_islr_xml_line(self):
        self.ensure_one()
        if self.is_purchase_document():
            query = '''
                SELECT move.id, line.id AS line_src_id, rec_line.id AS rec_line_id,
                rec_line.payment_id, rec_line.journal_id, rec_line.date,
                move.ref, payment.amount, identification.l10n_ve_code, partner.vat,
                payment.comment_withholding, seniat.code_seniat,
                payment.withholding_base_amount,
                pay_group.regimen_islr_id
                FROM account_move move
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                JOIN account_move_line rec_line ON
                    (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                JOIN account_payment payment ON payment.id = rec_line.payment_id
                JOIN account_journal journal ON journal.id = rec_line.journal_id
                JOIN account_journal_outbound_payment_method_rel outbound ON journal.id = outbound.journal_id
                JOIN account_payment_method pay_method ON pay_method.id = outbound.outbound_payment_method
                JOIN account_tax tax ON tax.id = payment.tax_withholding_id
                JOIN res_partner partner ON partner.id = move.partner_id
                JOIN l10n_latam_identification_type identification ON identification.id = partner.l10n_latam_identification_type_id
                JOIN account_payment_group pay_group ON pay_group.id = payment.payment_group_id
                JOIN seniat_tabla_islr seniat ON seniat.id = pay_group.regimen_islr_id
                WHERE payment.state IN ('posted', 'sent')
                AND journal.type = 'cash'
                AND move.id = %s
                AND pay_method.code='withholding'
                AND tax.type_tax_use='supplier'
                AND tax.withholding_type='tabla_islr'
            UNION
                SELECT move.id, line.id AS line_src_id, rec_line.id AS rec_line_id,
                rec_line.payment_id, rec_line.journal_id, rec_line.date,
                move.ref, payment.amount, identification.l10n_ve_code, partner.vat,
                payment.comment_withholding, seniat.code_seniat,
                payment.withholding_base_amount,
                pay_group.regimen_islr_id
                FROM account_move move
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                JOIN account_move_line rec_line ON
                    (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                JOIN account_payment payment ON payment.id = rec_line.payment_id
                JOIN account_journal journal ON journal.id = rec_line.journal_id
                JOIN account_journal_inbound_payment_method_rel inbound ON journal.id = inbound.journal_id
                JOIN account_payment_method pay_method ON pay_method.id = inbound.inbound_payment_method
                JOIN account_tax tax ON tax.id = payment.tax_withholding_id
                JOIN res_partner partner ON partner.id = move.partner_id
                JOIN l10n_latam_identification_type identification ON identification.id = partner.l10n_latam_identification_type_id
                JOIN account_payment_group pay_group ON pay_group.id = payment.payment_group_id
                JOIN seniat_tabla_islr seniat ON seniat.id = pay_group.regimen_islr_id
                WHERE payment.state IN ('posted', 'sent')
                AND journal.type = 'cash'
                AND move.id = %s
                AND pay_method.code='withholding'
                AND tax.type_tax_use='customer'
                AND tax.withholding_type='tabla_islr'


            '''
            params = [self.id, self.id]
            self._cr.execute(query, params)
            res = self._cr.dictfetchone()
            if res:
                amount = res['amount']
                code = res['code_seniat']
                rate = res['comment_withholding'].split("%")[0]
                rif = "{}{}".format(res['l10n_ve_code'], res['vat'])
                date = res['date'].strftime("%Y-%m-%d")
                nro_fact = res['ref']
                nro_ctrl = res['ref']
                mov_line = res['rec_line_id']
                concept = res['regimen_islr_id']
                base_wh = res['withholding_base_amount']

                #xml_doc_id,
                return {
                    'concept_id': concept,
                    'partner_vat': rif,
                    'invoice_number': nro_fact,
                    'control_number': nro_ctrl,
                    'concept_code': code,
                    'porcent_rete': rate,
                    'wh': amount,
                    'base': base_wh,
                    'move_id': self.id,
                    'move_line_id': mov_line,
                    'type': 'invoice',
                    'date': date
                }
        return {}

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------


    def _get_withheld_payments(self):
        self.ensure_one()
        inv_mov_lines = self.line_ids.filtered(
            lambda m: m.exclude_from_invoice_tab and
            m.account_internal_type=='payable'
        )
        if self.is_outbound():
            partial_lines = inv_mov_lines.mapped('matched_debit_ids')
            payment_mov_lines = partial_lines.mapped('debit_move_id')
        else:
            partial_lines = inv_mov_lines.mapped('matched_credit_ids')
            payment_mov_lines = partial_lines.mapped('credit_move_id')

        wh_payments = payment_mov_lines.mapped('payment_id').filtered(
            lambda p: p.payment_method_id.code=='withholding'
        )
        return wh_payments

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'xml_line_ids.xml_doc_id.state')
    def _compute_withheld_state(self):
        self.env['account.payment'].flush(['state'])
        self.env['seniat.islr.xml'].flush(['state'])
        for move in self:
            if move.is_invoice():
                move.invoice_withholding_islr_state = 'not_apply'
                if move.is_purchase_document():
                    #buscamos en las lineas de factura sí hay servicios
                    for line in move.invoice_line_ids:
                        # TODO debería agregarse al apunte (account.move.line)
                        # un campo many2one a la tabla de conceptos
                        # (seniat.tabla.islr) esto permitiría conocer
                        # de manera sencilla y con seguridad si la factura
                        # debe retenerse. Asi mismo debe agregarse este campo
                        # al modelo de produtos y al de las categorias lo que
                        # permitiría comportarse de manera similar a como
                        # ocurre con el campo account el cual es tomado del
                        # producto o en su defecto de la categoría del mismo.
                        if line.product_id and \
                            line.product_id.type=='service':
                            move.invoice_withholding_islr_state = 'not_held'
                            break

                wh_payments = move._get_withheld_payments()
                #recorremos los pagos de retencion
                for p in wh_payments:
                    #retencion ISLR
                    if p.tax_withholding_id.withholding_type=='tabla_islr':
                        move.invoice_withholding_islr_state = 'in_progress'
                        if move.is_sale_document():
                            move.invoice_withholding_islr_state = 'held'

                        domain = [
                            ('xml_doc_id.state', '=', 'done'),
                            ('move_id', '=', move.id)
                        ]
                        xml_lines = self.env['seniat.islr.xml.line']
                        xml_line_done = xml_lines.search(domain)
                        #pregutamos si ya esta declarada
                        if xml_line_done:
                            move.invoice_withholding_islr_state = 'held'

            else:
                move.invoice_withholding_islr_state = False