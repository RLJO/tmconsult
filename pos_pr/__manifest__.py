# -*- coding: utf-8 -*-
{
    'name': "POS Payment Register",

    'summary': """ Implements a payment register in POS """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Eduwebgroup",
    'website': "https://www.eduwebgroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/Point Of Sale',
    'version': '1.3.0',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'eduweb_js_utils',
                'point_of_sale'],

    'data': [
        'security/ir.model.access.csv',

        'data/products.xml',
        'data/sequence.xml',

        'views/assets.xml',
        'views/invoice_payment_views.xml',

        'views/pos_session_views.xml',
        'views/pos_config_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
        'views/account_bank_statement_cashbox_views.xml',

        'views/res_config_settings_views.xml',
        'views/pos_payment_method_views.xml',
    ],

    'qweb': [
        # Core
        'static/src/xml/core/chrome.xml',

        # Payment receipt
        'static/src/xml/templates/payment_reports.xml',
        'static/src/xml/templates/surcharge_reports.xml',

        'static/src/xml/screens/invoice_payment_receipt.xml',
        'static/src/xml/screens/surcharge_payment_receipt.xml',

        'static/src/xml/pos_view.xml',

        # owl Views
        'static/src/xml/owl/invoice_payment_screens.xml'
    ],    
    'post_init_hook': 'update_wrong_surcharge_journal_in_configs',
}
