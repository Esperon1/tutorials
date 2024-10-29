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
        base_domain = [('type', '=', 'solution')]
        domain = base_domain
        if tags:
            # Convert the comma-separated tag IDs to a list of integers
            tag_ids = [int(tag_id) for tag_id in tags.split(',') if tag_id.isdigit()]
            if tag_ids:
                # Add a condition for each tag to the domain
                for tag_id in tag_ids:
                    domain.append(('tags', '=', tag_id))

        solutions = request.env['solution_search.solution'].search(domain)

        # get all tags for all solutions
        all_solutions = request.env['solution_search.solution'].search(base_domain)
        tags = all_solutions.mapped('tags')
        categories = tags.mapped('category_id')

        return request.render('solution_search.solutions_view', {
            'solutions': solutions,
            'categories': categories,
            'tags': tags,
            'current_page': page,
        })

    @http.route([
        '/papers',
        '/papers/page/<int:page>',
        '/papers/tag/<string:tags>',
        '/papers/tag/<int:tag>/page/<int:page>'], auth='public', website=True)
    def show_papers(self, tags=False, page=1, **kw):
        base_domain = [('type', '=', 'paper')]
        domain = base_domain

        if tags:
            # Convert the comma-separated tag IDs to a list of integers
            tag_ids = [int(tag_id) for tag_id in tags.split(',') if tag_id.isdigit()]
            if tag_ids:
                # Add a condition for each tag to the domain
                for tag_id in tag_ids:
                    domain.append(('tags', '=', tag_id))

        papers = request.env['solution_search.solution'].search(domain)

        # get all tags for all papers
        all_papers = request.env['solution_search.solution'].search(base_domain)
        tags = all_papers.mapped('tags')
        categories = tags.mapped('category_id')

        return request.render('solution_search.papers_view', {
            'solutions': papers,
            'categories': categories,
            'tags': tags,
            'current_page': page,
        })
