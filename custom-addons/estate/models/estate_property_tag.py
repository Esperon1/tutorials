from odoo import models, fields, api


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'
    _order = 'name'

    name = fields.Char(required=True, help="Enter the name of the property tag")
    property_ids = fields.Many2many('estate.property', string="Properties")
    property_count = fields.Integer(compute='_compute_property_count', string="Property Count")
    color = fields.Integer()

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'The name of the property tag must be unique')
    ]
    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)
