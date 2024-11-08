from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'
    _order = 'price DESC'

    name = fields.Char(required=True, help="Enter the name of the offer", string="Title", default="New")
    create_date = fields.Datetime(default=fields.Datetime.now, help="Enter the creation date of the offer")
    price = fields.Float(required=True, help="Enter the price of the offer", string="Price")
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], copy=False)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    property_id = fields.Many2one('estate.property', string="Property", required=True)
    validity = fields.Integer(help="Enter the validity of the offer in days", string="Validity (days)", default=7)
    date_deadline = fields.Date(help="Enter the deadline of the offer", string="Deadline", required=True,
                                inverse='_inverse_date_deadline', compute='_compute_date_deadline')

    # Thanks to this field, an offer will be linked to a property type when it’s created
    property_type_id = fields.Many2one(related='property_id.property_type_id', string="Property Type", store=True)

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for record in self:
            if not record.create_date:
                record.create_date = fields.Datetime.now()

            create_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = create_date + relativedelta(days=record.validity or 0)

    def _inverse_date_deadline(self):
        for record in self:
            create_date = record.create_date.date() if record.create_date else fields.Date.today()
            if record.date_deadline:
                delta = record.date_deadline - create_date
                record.validity = delta.days
            else:
                record.validity = 0

    def action_accept(self):
        estate_property = self.env['estate.property'].browse(self.property_id.id)
        for record in self:
            if estate_property.state not in ['canceled', 'sold']:
                record.status = 'accepted'
                record.property_id.selling_price = record.price
                record.property_id.buyer_id = record.partner_id.id
                estate_property.state = 'offer_accepted'
                estate_property.partner_id = record.partner_id.id
            else:
                raise UserError(f'You cannot sell a {estate_property.state} property.')

    def action_refuse(self):
        for record in self:
            record.status = 'refused'
            record.property_id.selling_price = 0

        return True

    #  in real life, only one offer can be accepted for a given property.
    @api.constrains('status')
    def _check_accepted_offer(self):
        for record in self:
            if record.status == 'accepted' and record.property_id.offer_ids.filtered(
                    lambda r: r.status == 'accepted' and r.id != record.id):
                raise ValidationError("You cannot accept multiple offers for the same property")

    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price < 0:
                raise ValidationError("The price of the offer must be greater than 0")
