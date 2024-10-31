from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    name = fields.Char(required=True, help="Enter the name of the property", string="Title", default="New")
    description = fields.Text(help="Enter a description for the property")
    postcode = fields.Char(help="Enter the postcode for the property", string="Postcode")

    # default availability date in 3 months
    availability_date = fields.Date(default=lambda self: fields.Date.today() + relativedelta(months=3),
                                    help="Enter the availability date", string="Available From")

    expected_price = fields.Float(required=True, help="Enter the expected price for the property",
                                  string="Expected Price")
    selling_price = fields.Float(readonly=True, copy=False, help="Enter the selling price for the property",
                                 string="Selling Price")
    bedrooms = fields.Integer(help="Enter the number of bedrooms in the property", default=2, string="Bedrooms")
    living_area = fields.Integer(help="Enter the living area in square meters", string="Living Area")
    facades = fields.Integer(help="Enter the number of facades")
    garage = fields.Boolean(help="Check if the property has a garage")
    garden = fields.Boolean(help="Check if the property has a garden")
    garden_area = fields.Integer(help="Enter the garden area in square meters")
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ], help="Select the garden orientation")
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ], required=True, string="Status", default='new', copy=False, help="Select the status of the property")
    active = fields.Boolean(default=True, help="Check if the property is active")
    last_seen = fields.Datetime(string="Last Seen", default=fields.Datetime.now, help="Enter the last seen date")
