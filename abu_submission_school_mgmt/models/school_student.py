import calendar
from datetime import date
from odoo import _, api, fields, models, Command

class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'School Student'

    name = fields.Char(string='Name', required=True, copy=False)
    nis = fields.Char(string='NIS', required=True, copy=False)
    partner_invoice_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    classroom_id = fields.Many2one(comodel_name='school.classroom', string='Classroom')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active', string='Status', required=True)
    account_move_ids = fields.One2many(comodel_name='account.move', inverse_name='student_id', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoice Count')

    _sql_constraints = [
        ('nis_uniq', 'unique (nis)', 'The NIS must be unique per student !'),
    ]

    def action_activate_student(self):
        for student in self:
            if student.status != 'active':
                student.status = 'active'

    def action_deactivate_student(self):
        for student in self:
            if student.status != 'inactive':
                student.status = 'inactive'

    def action_view_account_move_ids(self):
        invoices = self.mapped('account_move_ids')
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_invoice_id.id,
                'default_student_id': self.id,
                'default_invoice_origin': self.name,
            })
        action['context'] = context
        return action

    @api.depends('account_move_ids')
    def _compute_invoice_count(self):
        for student in self:
            student.invoice_count = len(student.account_move_ids)

    @api.model
    def create(self, vals):
        if 'partner_invoice_id' not in vals:
            partner_invoice_id = self.env['res.partner'].create({
                'name': vals['name'],
                'customer_rank': 1
            })
            vals['partner_invoice_id'] = partner_invoice_id.id
        return super(SchoolStudent, self).create(vals)
    
    def _prepare_spp_product_values(self):
        self.ensure_one()
        return {
            'name': _('Pembayaran Bulanan'),
            'type': 'service',
            'company_id': False,
            'taxes_id': False,
        }
    
    def _get_spp_product(self):
        spp_product_id = int(self.env['ir.config_parameter'].sudo().get_param('abu_submission_school_mgmt.default_spp_product_id'))
        if not spp_product_id:
            spp_product_id = self.env['product.product'].create(
                self._prepare_spp_product_values()
            ).id
            self.env['ir.config_parameter'].sudo().set_param('abu_submission_school_mgmt.default_spp_product_id', spp_product_id)
        return spp_product_id

    def _prepare_student_invoice_vals(self):
        self.ensure_one()
        today = fields.Date.today()
        company, user = self.env.company, self.env.user  # Combine assignments

        spp_product_id = self._get_spp_product()

        return {
            'ref': '',
            'move_type': 'out_invoice',
            'invoice_date': today,
            'student_id': self.id,
            'currency_id': company.currency_id.id,
            'partner_id': self.partner_invoice_id.id,
            'invoice_origin': self.name,
            'invoice_user_id': user.id,
            'company_id': company.id,
            'user_id': user.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': spp_product_id,
                    'name': f'Biaya Penyelenggaraan - {today.strftime("%b").title()} {today.year}/{today.year+1}',
                    'quantity': 1,
                    'price_unit': 50000,
                    'tax_ids': False
                })
            ]
        }

    def _find_existing_invoices(self, month, year, active_students):
        date_start = date(year, month, 1)
        date_end = date(year, month, calendar.monthrange(year, month)[1])
        return self.env['account.move'].search([
            ('invoice_date', '>=', date_start),
            ('invoice_date', '<=', date_end),
            ('student_id', 'in', active_students.ids)
        ])

    def _generate_student_invoice_per_month(self):
        print('...... start _generate_student_invoice_per_month ......')
        today = fields.Date.today()
        active_students = self.env['school.student'].search([('status', '=', 'active')])
        existing_invoices = self._find_existing_invoices(today.month, today.year, active_students)
        for student in active_students.filtered(lambda s: s not in existing_invoices.mapped('student_id')):
            self.env['account.move'].create(student._prepare_student_invoice_vals())
        print('...... end _generate_student_invoice_per_month ......')
