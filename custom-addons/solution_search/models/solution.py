from odoo import models, fields, api, _
from odoo.tools.translate import html_translate


class SolutionSearchSolution(models.Model):
    _name = 'solution_search.solution'
    _description = 'Entry'
    _inherit = [
        'mail.thread',
        'website.seo.metadata',
        'website.multi.mixin',
        'website.cover_properties.mixin',
        'website.searchable.mixin',
        'image.mixin'
    ]

    _order = 'create_date DESC'

    type = fields.Selection([('paper', 'Paper'), ('solution', 'Solution')], default='solution', change_default=True)

    active = fields.Boolean(string='Active', default=True)

    solution_subtitle = fields.Char(string='Subtitle', translate=True)  # Subtitle of the solution (optionally)

    name = fields.Char(string='Solution Name', required=True, translate=True)  # Name of the solution
    description = fields.Html(string='Content', translate=html_translate, sanitize=False)  # Description of the solution
    long_description = fields.Html(string='Long Description', translate=html_translate, sanitize=False)  # Long description of the solution
    video = fields.Char(string='Video URL')  # Video URL for the solution
    tags = fields.Many2many('solution_search.tag', string='Tags', required=True)  # Tags for the solution




