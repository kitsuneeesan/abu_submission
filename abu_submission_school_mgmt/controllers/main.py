import json
from odoo.http import Controller, request, route
from werkzeug.exceptions import BadRequest

class SchoolController(Controller):

    @route('/school-mgmt/teachers', auth="api_key", methods=['GET'])
    def teachers_get(self):
        teachers = request.env['school.teacher'].search([])
        return request.make_json_response(teachers.read())

    @route('/school-mgmt/add-student', auth="api_key", methods=['POST'], type='json')
    def student_add(self, **kwargs):
        if kwargs:
            try:
                classroom = kwargs['classroom']
                classroom_id = request.env['school.classroom'].search([('name', '=', classroom)])
                if classroom_id:
                    student = kwargs['student']
                    student_exists = request.env['school.student'].search([('nis', '=', student['nis'])])
                    if student_exists:
                        return {'success': False, 'error': 'Student NIS %s already exists' % (student['nis'])}
                    student_vals = {
                        'nis': student['nis'],
                        'name': student['name'],
                        'classroom_id': classroom_id.id
                    }
                    student_id = request.env['school.student'].create(student_vals)
                    return {
                        'success': True, 
                        'result':  student_vals, 
                        'message': f'Success add new student to classroom {classroom}'
                    }
                else:
                    return {'success': False, 'error': f'Classroom {classroom} not found'}
            except Exception as err:
                return {'success': False, 'error': f'Params {err} is required, but it missing'}
        else:
            raise BadRequest('No Body Request')