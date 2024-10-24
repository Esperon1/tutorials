# controller to show all solutions on the website under url /solutions

from odoo import http
from odoo.http import request


class Solution(http.Controller):
    # narrow down the search by tag (filtering)

    @http.route([
        '/solutions',
        '/solutions/page/<int:page>',
        '/solutions/tag/<string:tags_id>',
        '/solutions/tag/<int:tag>/page/<int:page>'], auth='public', website=True)
    def show_solutions(self, tags=False, page=1, **kw):
        domain = []

        if tags:
            # Convert the comma-separated tag IDs to a list of integers
            tag_ids = [int(tag_id) for tag_id in tags.split(',') if tag_id.isdigit()]
            if tag_ids:
                # Add a condition for each tag to the domain
                for tag_id in tag_ids:
                    domain.append(('tags_id', '=', tag_id))

        solutions = request.env['solution_search.solution'].search(domain)

        # get all tags_id for all solutions
        all_solutions = request.env['solution_search.solution'].search([])
        tags = all_solutions.mapped('tags_id')
        categories = tags.mapped('category_id')

        return request.render('solution_search.solutions_view', {
            'solutions': solutions,
            'categories': categories,
            'tags_id': tags,
            'current_page': page,
        })
