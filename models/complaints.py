from openerp import api, fields, models, _
import datetime

class HrComplaints(models.Model):
    _name = 'hr.complaints'

    complaint_against = fields.Many2one('hr.employee', 'Complaint Against Employee', required=True)
    complainer = fields.Many2one('hr.employee', 'Employee lodging a Complaint', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee lodging a Complaint', readonly=True)
    date = fields.Date('Complaint date')
    note = fields.Text(string="Note",required=True)
    disc_attach = fields.Binary('Reference Documents')
    anonymous_user = fields.Boolean('Anonymous User', default=None,help="Be anonymous")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('done', 'Done'),
    ], string='Status', readonly=True, track_visibility='onchange', default='draft')
    
    
    @api.onchange('anonymous_user')
    def onchange_anonymous_user(self):
        if not self.anonymous_user:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if hr_employee:
                hr_employee = hr_employee[0]
                self.complainer = hr_employee.id
        else:
            self.complainer = False
            
    @api.model
    def create(self, vals):
        hr_employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if hr_employee:
            hr_employee = hr_employee[0]
            vals['employee_id'] = hr_employee.id
        
        if not vals.get('anonymous_user'):
            if hr_employee:
                hr_employee = hr_employee[0]
                vals['complainer'] = hr_employee.id
        else:
            vals['complainer'] = False
        return super(HrComplaints,self).create(vals)
     
    @api.multi
    def write(self, vals):
        if 'anonymous_user' in vals.keys():
            hr_employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if hr_employee:
                hr_employee = hr_employee[0]
                vals['employee_id'] = hr_employee.id
            
            if not vals.get('anonymous_user'):
                if hr_employee:
                    hr_employee = hr_employee[0]
                    vals['complainer'] = hr_employee.id
            else:
                vals['complainer'] = False
        return super(HrComplaints,self).write(vals)
    
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.complaints'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.complaints', 'default_res_id': self.id}
        return res
    
    #   this below method is to send the complaint mail to all the Hr officer group
    @api.multi
    def submit_mail(self):
        ir_attachment_obj = self.env['ir.attachment'].search([('res_id', '=', self.id)])
        groups_obj = self.env.ref("hr.group_hr_user").users
        hr_template_id = self.env['ir.model.data'].get_object('indian_payroll', "hr_mail_complaints")
        complainer_template_id = self.env['ir.model.data'].get_object('indian_payroll', "emp_mail_complaints")
        hr_template_id.attachment_ids = None
        for attachment_obj in ir_attachment_obj:
            if attachment_obj.id:
                hr_template_id.attachment_ids = [attachment_obj.id]
        for i in groups_obj:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', i.id)])
            if hr_employee:
                if hr_employee.work_email:
                    self.hr_manager_email_id = hr_employee.work_email
                    self.env['mail.template'].browse(hr_template_id.id).send_mail(self.id, force_send=True)
        self.env['mail.template'].browse(complainer_template_id.id).send_mail(self.id, force_send=True)
        self.state = 'submitted'

    @api.multi
    def close_mail_send(self):
        groups_obj = self.env.ref("hr.group_hr_user").users
        template_id = self.env['ir.model.data'].get_object('indian_payroll', "hr_mail_complaints_closed")
        complainer_template_id = self.env['ir.model.data'].get_object('indian_payroll', "emp_mail_complaints_closed")
        for i in groups_obj:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', i.id)])
            if hr_employee:
                if hr_employee.work_email:
                    self.hr_manager_email_id = hr_employee.work_email
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
        self.env['mail.template'].browse(complainer_template_id.id).send_mail(self.id, force_send=True)
        self.state = 'done'