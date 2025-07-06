from odoo import _, api, fields, models

class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'School Teacher'

    name = fields.Char(string='Name', required=True, copy=False)
    nip = fields.Char(string='NIP', required=True, copy=False)
    street = fields.Char(required=True)
    street2 = fields.Char()
    zip = fields.Char(change_default=True, required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]", required=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', required=True)
    country_code = fields.Char(related='country_id.code', string="Country Code")
    email = fields.Char()
    phone = fields.Char(unaccent=False, required=True, copy=False)
    total_students = fields.Integer(compute='_compute_total_students', string='Students', help='The number of students taught by this teacher')
    
    _sql_constraints = [
        ('phone_uniq', 'unique (phone)', 'The phone number must be unique per teacher !'),
        ('nip_uniq', 'unique (nip)', 'The NIP must be unique per teacher !'),
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(
            default or {},
            name=_('%s (copy)' % self.name),
            nip=_('%s (copy)' % self.nip),
            phone=('%s (copy)' % self.phone)
        )
        return super(SchoolTeacher, self).copy(default=default)

    def _compute_total_students(self):
        for teacher in self:
            classroom_ids = self.env['school.classroom'].search([('teacher_ids', 'in', teacher.id)])
            teacher.total_students = sum([len(classroom.student_ids) for classroom in classroom_ids])