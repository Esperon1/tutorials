from odoo import models, fields, api


class SolutionTagCategory(models.Model):
    _name = 'solution.tag.category'
    _description = 'Solution Tag Category'
    _inherit = ['website.seo.metadata']

    name = fields.Char(string='Name', required=True, translate=True)
    tag_ids = fields.One2many('solution.tag', 'category_id', string='Tags')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Category name already exists!')
    ]
