# -*- coding: utf-8 -*-
{
    'name': "l10n_at_pos_cert",

    'summary': "Integration of Fiskaly API for POS in Austria",

    'description': """This module integrates the Fiskaly API to ensure POS transactions in Austria comply with local fiscal laws. It manages the creation of Signature Creation Units (SCUs), Cash Registers, and signing receipts.

    """,

    'author': "Multioss GmbH",
    'website': "https://www.multioss.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Point of Sale',
    'version': '0.201',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'l10n_at'],

    'assets': {
        'web.assets_backend': [
            'l10n_at_pos_cert/static/src/js/decommission_warning.js',
        ],
        'point_of_sale._assets_pos': [
            'l10n_at_pos_cert/static/src/**/*',
        ]
    },

    # always loaded in certain order. !!!Keep in mind that the order of the modules is important!!!
    'data': [
        'views/res_company_views.xml',
        'views/res_config_settings.xml',
        'views/pos_order.xml',
        'wizard/dep7_data_export_audit_wizard_views.xml',
        'views/point_of_sale_dashboard.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml'
    ],
    'installable': True,
}
