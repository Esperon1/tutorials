from odoo import models, fields, api
from odoo.addons.test_convert.tests.test_env import field


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, help="Enter the name of the property type")
    property_ids = fields.One2many(comodel_name='estate.property', inverse_name='property_type_id', string='Properties')
    sequence = fields.Integer(help="Enter the sequence of the property type", string="Sequence", default=1)
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'The name of the property type must be unique')
    ]



