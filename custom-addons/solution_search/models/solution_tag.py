from odoo import models, fields, api


class SolutionTag(models.Model):
    _name = 'solution_search.tag'
    _description = 'Solution Tag'
    _inherit = ['website.seo.metadata']

    name = fields.Char(string='Name', required=True)
    category_id = fields.Many2one('solution_search.tag.category', string='Category')
    solution_ids = fields.Many2many('solution_search.solution', string='Solution')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name already exists!')
    ]

