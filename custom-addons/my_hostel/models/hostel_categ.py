from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HostelCategory(models.Model):
    _name = 'hostel.category'
    _description = 'Information about hostel category'
    _parent_store = True
    _parent_name = 'parent_id'
    name = fields.Char('Category')
    parent_path = fields.Char(index=True)

    # You should use this technique for hierarchies that do not change much but are read and queried a
    # lot.
    # If you have a hierarchy that changes a lot, you might get better performance by using the standard
    # parent_id and child_ids relationships. p95.
    parent_id = fields.Many2one('hostel.category',
                                string='Parent Category',
                                ondelete='restrict',
                                index=True)

    child_ids = fields.One2many('hostel.category', 'parent_id', string='Child Categories')

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError('Error! You cannot create recursive categories.')

    def unlink(self):
        res = super(HostelCategory, self).unlink()
        remaining_records = self.search([])
        if not remaining_records:
            # Reset the sequence of the 'id' field
            self.env.cr.execute("SELECT setval(pg_get_serial_sequence('hostel_category','id'), 1, false);")
            # Reset parent_path if needed
            self.env.cr.execute("UPDATE hostel_category SET parent_path = '0'")
        return res
