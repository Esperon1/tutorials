from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HostelRoom(models.Model):
    _name = 'hostel.room'
    _description = 'Information about hostel room'
    _rec_name = 'room_number'

    room_name = fields.Char('Room Name', help='Enter the name of the room', required=True)
    room_number = fields.Char('Room No', help='Enter the room number', required=True)
    floor_number = fields.Integer('Floor Number', help='Enter the floor number of the room')
    rent_amount = fields.Monetary('Rent Amount', currency_field='currency_id', help='Enter the rent amount per month')
    currency_id = fields.Many2one('res.currency', string='Currency')

    hostel_id = fields.Many2one('hostel.hostel', string='Name of Hostel',
                                required=True)  # hostel_id is a many2one field that will store the hostel id.

    student_ids = fields.One2many('hostel.student', 'room_id', string='Students',
                                  help='Select the students for the room')
    hostel_amenities_ids = fields.Many2many('hostel.amenities', 'hostel_room_amenities_rel', 'room_id', 'amenity_id',
                                            string='Amenities', domain=[('active', '=', True)],
                                            help='Select the amenities for the room')

    student_per_room = fields.Integer("Student Per Room",
                                      required=True,
                                      help="Students allocated per room.")
    availability = fields.Float(compute='_compute_availability', string='Availability', help='Availability of the room',
                                store=True)

    # We want to make sure that our models do not have invalid or inconsistent data
    _sql_constraints = [
        ('room_number_uniq', 'unique(room_number)', 'Room number must be unique!'),
    ]

    @api.depends('room_number')
    def _compute_display_name(self):
        """This function creates a name for the record based on the room name and room number."""
        for record in self:
            name = record.room_name
            if record.room_number:
                name = f'{name} ({record.room_number})'

            record.display_name = name

    # method to check condition on a set of records.
    # Automatically called when the rent_amount field is updated.
    @api.constrains('rent_amount')
    def _check_rent_amount(self):
        """This function checks if the rent amount is greater than 0."""
        if self.rent_amount < 0:
            raise ValidationError(_('Rent amount must be greater than 0!'))

    # computes the availability of rooms based on student occupancy.
    @api.depends('student_per_room', 'student_ids')
    def _compute_availability(self):
        """This function computes the availability of rooms based on student occupancy."""
        for record in self:
            record.availability = record.student_per_room - len(record.student_ids)
