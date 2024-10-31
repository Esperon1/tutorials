from odoo import models, fields, api


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'

    name = fields.Char(required=True, help="Enter the name of the property tag")
    property_ids = fields.Many2many('estate.property', string="Properties")
    property_count = fields.Integer(compute='_compute_property_count', string="Property Count")

    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)
