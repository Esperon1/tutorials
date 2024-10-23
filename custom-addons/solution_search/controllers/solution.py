# controller to show all solutions on the website under url /solutions

from odoo import http
from odoo.http import request


class Solution(http.Controller):
    # narrow down the search by tag (filtering)

    @http.route([
        '/solutions',
        '/solutions/page/<int:page>',
        '/solutions/tag/<string:tags>',
        '/solutions/tag/<int:tag>/page/<int:page>'], auth='public', website=True)
    def show_solutions(self, tags=False, page=1, **kw):
        domain = []

        if tags:
            tag_ids = [int(tag_id) for tag_id in
                       tags.split(',')]  # allow a string of tag ids separated by commas, to filter by multiple tags
            if tag_ids:
                domain.append(('tags', 'in', tag_ids))

        solutions = request.env['solution_search.solution'].search(domain)
        # get all categories
        categories = request.env['solution_search.tag.category'].search([])

        return request.render('solution_search.solutions_view', {
            'solutions': solutions,
            'categories': categories,
            'current_page': page,
            'tags': tags,
        })
