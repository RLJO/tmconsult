# -*- coding: utf-8 -*-
{
    'name': "Company Structure",

    'summary': """ Company tree structure """,

    'description': """ Company tree structure """,

    'author': "Eduwebgroup",
    'website': "https://www.eduwebgroup.com",

    'category': 'Accounting',
    'version': '1.1',

    'depends': ['contacts', 'account_accountant'],

    'data': [
        'views/inherited/res_partner_views.xml',
    ],

    'currency': 'USD',
    'license': 'OPL-1',
    'price': 30,
    'images': [
                'static/description/description.png',
                'static/description/Image01.png'
    ],
}
