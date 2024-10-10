from odoo import fields, models, api
from datetime import timedelta


class HostelStudent(models.Model):
    _name = 'hostel.student'
    _description = 'Information about hostel student'
    name = fields.Char('Student Name', required=True)

    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'), ('other', 'Other')
    ], string='Gender', help='Select the gender')
    active = fields.Boolean('Active', default=True,
                            help='If unchecked, it will allow you to hide the student without removing it.')

    room_id = fields.Many2one('hostel.room', string='Room', help='Select the room for the student')
    amenity_id = fields.Many2one('hostel.amenities', string='Amenity',
                                 help='Select the amenity for the student')

    # fields for computed values
    admission_date = fields.Date('Admission Date', help='Enter the admission date of the student',
                                 default=fields.Datetime.today)
    discharge_date = fields.Date('Discharge Date', help='Enter the discharge date of the student')

    duration = fields.Integer('Duration', compute='_compute_check_duration', inverse='_inverse_duration',
                              help='Enter the duration of stay in months')

    # exposing related fields stored in other models p100

    # Odoo clients can only read data from the server for the fields that belong to the model they are querying.
    # They cannot access data from related tables using dot notation as server-side code can.

    # However, we can make the data from related tables available to the clients by adding it as related fields.
    # This is what we will do to get the hostel of the room in the student model.

    hostel_id = fields.Many2one('hostel.hostel', string='Hostel', related='room_id.hostel_id', store=True,
                                help='Hostel of the room')

    @api.depends('admission_date', 'discharge_date')
    def _compute_check_duration(self):
        for record in self:
            if record.admission_date and record.discharge_date:
                record.duration = (record.discharge_date - record.admission_date).days

    def _inverse_duration(self):
        for student in self:
            if student.discharge_date and student.admission_date:
                duration = (student.discharge_date - student.admission_date).days

                if duration != student.duration:
                    student.discharge_date = (student.admission_date + timedelta(days=student.duration)).strftime(
                        '%Y-%m-%d')

    # Make sure that the compute method always assigns a value to the computed field. Otherwise, an error
    # will occur. This can happen when you have conditions in your code that sometimes fail to assign a
    # value to the computed field. This can be hard to debug.

    # It is also possible to make a non-stored computed field searchable by setting the search attribute to
    # the method name (similar to compute and inverse). Like inverse, search is also optional;
    # if you don’t want to make the computed field searchable, you can skip it.
