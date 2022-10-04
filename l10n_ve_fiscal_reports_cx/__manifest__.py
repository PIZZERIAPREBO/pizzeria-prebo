# -*- coding: utf-8 -*-

{
    'name': 'Venezuela Fiscal Reports',
    'author': "CIEXPRO",
    'website': "https://www.ciexpro.com",
    'version' : '1.0',
    'sequence': 1,
    'category' : 'Localization',
    'description' : """
    This module adds the tax reports required by Venezuelan laws

    """,

    'depends': [
        'account',
        'l10n_ve_withholding'
    ],
    'data': [
        'security/fiscal_reports_security.xml',
        'security/ir.model.access.csv',
        'reports/seniat_purchase_ledger_report.xml',
        'reports/seniat_sale_ledger_report.xml',
        'reports/account_daily_ledger_report.xml',
        'reports/account_analytical_ledger_report.xml',
        'reports/account_balance_check_report.xml',
        'reports/report.xml',
        'views/account_tax_view.xml',
        'views/seniat_vat_ledger_view.xml',
        'views/seniat_iva_txt_view.xml',
        'views/seniat_islr_xml_view.xml',
        'wizard/ve_fiscal_report_daily_ledger_view.xml',
        'wizard/ve_fiscal_report_analytical_ledger_view.xml',
        'wizard/ve_financial_report_balance_check_view.xml',
    ],
    'installable': True,
}

