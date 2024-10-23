from odoo import models, fields, api, _
from odoo.tools.translate import html_translate


class SolutionSearchSolution(models.Model):
    _name = 'solution_search.solution'
    _description = 'Solution'
    _inherit = [
        'mail.thread',
        'website.seo.metadata',
        'website.multi.mixin',
        'website.cover_properties.mixin',
        'website.searchable.mixin',
    ]

    _order = 'create_date DESC'
    active = fields.Boolean(string='Active', default=True)

    solution_subtitle = fields.Char(string='Subtitle', translate=True)  # Subtitle of the solution (optionally)

    name = fields.Char(string='Solution Name', required=True, translate=True)  # Name of the solution
    description = fields.Html(string='Content', translate=html_translate, sanitize=False)  # Description of the solution
    video = fields.Char(string='Video URL')  # Video URL for the solution
    tags = fields.Many2many('solution_search.tag', string='Tags', required=True)  # Tags for the solution




