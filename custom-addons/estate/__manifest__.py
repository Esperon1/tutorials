{   'name': 'Estate Management',
     'version': '18.0.1.0',
     'category': 'Real Estate',
     'summary': 'Manage Real Estate Properties',

     'depends': ['base'],

     'data': [
         'security/ir.model.access.csv',
         'views/estate_property_views.xml',
         'views/estate_property_tag_views.xml',
         'views/estate_property_offer_views.xml',
         'views/estate_property_types_view.xml',
         'views/estate_menus.xml',
     ],

     'assets': {
         'web.assets_backend': [
             'estate/static/src/**/*',
         ]
     },

     'application': True,
     'installable': True
}
