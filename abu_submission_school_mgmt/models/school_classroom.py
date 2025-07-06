from odoo import fields, models

class SchoolClassroom(models.Model):
    _name = 'school.classroom'
    _description = 'School Classroom'

    name = fields.Char(string='Name', required=True)
    date_start = fields.Date()
    date_end = fields.Date()
    student_ids = fields.One2many(comodel_name='school.student', inverse_name='classroom_id', string='Students')
    teacher_ids = fields.Many2many(
        comodel_name='school.teacher', relation='school_classroom_teacher_ids_rel',
        column1='classroom_id', column2='teacher_id', string='Lesson Teachers'
    )
    teacher_id = fields.Many2one(comodel_name='school.teacher', string='Homeroom Teacher')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The classroom name must be unique !')
    ]