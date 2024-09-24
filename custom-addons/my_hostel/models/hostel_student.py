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
