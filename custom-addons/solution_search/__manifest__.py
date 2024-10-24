{
    'name': 'Solution Search',
    'summary': 'Solution Search',
    'description': 'Module to search for solutions (examples) on the website',
    'category': 'Website',
    'version': '1.2',
    'depends': ['website', 'website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'views/solution_views.xml',
        'views/templates.xml'
    ],

    'assets': {
        'web.assets_frontend': [
            'solution_search/static/src/scss/solutions.scss',
            'solution_search/static/src/js/shuffle.js',
            'solution_search/static/src/js/solutions.js',
        ]
    },

    'installable': True,
}
