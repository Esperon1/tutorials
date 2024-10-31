from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    partner_id = fields.Many2one('res.partner', string="Owner", required=True)
    name = fields.Char(required=True, help="Enter the name of the property", string="Title", default="New")
    description = fields.Text(compute="", help="Enter a description for the property")
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

    property_type_id = fields.Many2one('estate.property.type', string="Property Type")
    salesperson_id = fields.Many2one('res.users', string="Salesman", default=lambda self: self.env.user.id)
    buyer_id = fields.Many2one('res.partner', string="Buyer", copy=False)
    tags_ids = fields.Many2many('estate.property.tag', string="Tags")

    offer_ids = fields.One2many('estate.property.offer', 'property_id', string="Offers")

    total_area = fields.Integer(compute='_compute_total_area', store=True, help="Total area of the property",
                                string="Total Area(sqm)", readonly=True)

    best_offer = fields.Float(compute='_compute_best_offer', store=True, string="Best Offer",
                              help="Best offer received")

    # compute total area
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    # compute the best offer
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            record.best_offer = max(record.offer_ids.mapped('price')) if record.offer_ids else 0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.description = "Property of " + self.partner_id.name

    @api.onchange('garden')
    def _onchange_garden(self):
        if not self.garden:
            self.garden_area = 0
            self.garden_orientation = False
