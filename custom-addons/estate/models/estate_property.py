from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'
    _order = 'id DESC'

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
    buyer_id = fields.Many2one('res.partner', string="Buyer", copy=False, readonly=True)
    tags_ids = fields.Many2many('estate.property.tag', string="Tags")

    offer_ids = fields.One2many('estate.property.offer', 'property_id', string="Offers")

    total_area = fields.Integer(compute='_compute_total_area', store=True, help="Total area of the property",
                                string="Total Area(sqm)", readonly=True)

    best_offer = fields.Float(compute='_compute_best_offer', store=True, string="Best Offer",
                              help="Best offer received")
    partner_id = fields.Many2one('res.partner', string="Owner", help="Enter the owner of the property")

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
        self.description = "Property of " + self.partner_id.name if self.partner_id else ""

    @api.onchange('garden')
    def _onchange_garden(self):
        if not self.garden:
            self.garden_area = 0
            self.garden_orientation = False

    def action_sold(self):
        if self.state == 'canceled':
            raise UserError("You cannot sell a canceled property")

        self.state = 'sold'

        return True

    def action_cancel(self):
        if self.state == 'sold':
            raise UserError("Property is already sold")

        self.state = 'canceled'

        return True

    @api.constrains('expected_price')
    def _validate_expected_price(self):
        for record in self:
            if record.expected_price < 0:
                raise ValidationError("The expected price must be non-negative")

    @api.constrains('selling_price')
    def _validate_selling_price(self):
        for record in self:
            if record.selling_price < 0:
                raise ValidationError("The selling price must be non-negative")

    @api.constrains('selling_price', 'expected_price')
    # Check if the selling price is at least 90% of the expected price
    def _check_selling_price(self):
        for record in self:
            if not float_is_zero(record.selling_price, precision_digits=2):
                expected_price_90 = 0.9 * record.expected_price
                if float_compare(record.selling_price, expected_price_90, precision_digits=2) < 0:
                    raise ValidationError("The selling price must be at least 90% of the expected price.")

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'canceled':
            vals['expected_price'] = 0
        return super(EstateProperty, self).write(vals)
