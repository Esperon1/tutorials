{
    'name': 'Estate Management',
    'version': '18.0.1.0',
    'category': 'Real Estate',
    'summary': 'Manage Real Estate Properties',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml'
    ],

    'application': True,
    'installable': True,
}
