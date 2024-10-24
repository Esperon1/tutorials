# -*- coding: utf-8 -*-
{
    'name': "Gallery View",
    'summary': """
        Starting module for "Master the Odoo web framework, chapter 3: Create a Gallery View"
    """,

    'description': """
        Starting module for "Master the Odoo web framework, chapter 3: Create a Gallery View"
    """,

    'version': '0.1',
    'application': True,
    'category': 'Tutorials/AwesomeGallery',
    'installable': True,
    'depends': ['web', 'contacts'],
    'demo': [
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'static/src/**/*',
        ],
    },
    'license': 'AGPL-3'
}
