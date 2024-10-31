from odoo import models, fields, api


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'

    name = fields.Char(required=True, help="Enter the name of the property type", string="Title")
    property_ids = fields.One2many('estate.property', 'property_type_id', string="Properties")
    property_count = fields.Integer(compute='_compute_property_count', string="Property Count")

    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)
