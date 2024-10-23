{
    'name': 'Solution Search',
    'summary': 'Solution Search',
    'description': 'Module to search for solutions (examples) on the website',
    'category': 'Website',
    'version': '1.1',
    'depends': ['website', 'website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'views/solution_views.xml',
        'views/templates.xml'
    ],

    'installable': True,
}
