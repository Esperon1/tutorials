# controller to show all solutions on the website under url /solutions

from odoo import http
from odoo.http import request


class Solution(http.Controller):

    @http.route([
        '/solutions',
        '/solutions/page/<int:page>',
        '/solutions/tag/<int:tag>',
        '/solutions/tag/<int:tag>/page/<int:page>'], auth='public', website=True)
    def show_solutions(self, tag=False, page=1, **kw):
        domain = []
        if tag:
            domain = [('tags', 'in', tag)]

        solutions = request.env['solution_search.solution'].search(domain)
        # get all categories
        categories = request.env['solution_search.tag.category'].search([])
        return request.render('solution_search.solutions_view', {
            'solutions': solutions,
            'categories': categories,
        })
