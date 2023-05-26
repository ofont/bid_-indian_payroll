from openerp import api, fields, models, _
from openerp.exceptions import UserError

class JobCandidate(models.Model):
    _name = "job.candidate"
    
    job_id = fields.Many2one('hr.job', 'Applying for Position', required=True)
    name = fields.Char('Name', required=True)
    mobile = fields.Char('Mobile', required=True)
    email = fields.Char('Email', required=True)
    emp_id = fields.Many2one('hr.employee', 'Referring Employee', required=True)
    pan = fields.Char('PAN Number')
    description = fields.Char('Description')
    Resume = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.applicant')], string='Resume', required=True)

    @api.model
    def message_get_reply_to(self, ids, default=None):
        """ Override to get the reply_to of the parent project. """
        candidates = self.sudo().browse(ids)
        aliases = self.env['hr.job'].message_get_reply_to(candidates.mapped('job_id').ids, default=default)
        return dict((candidate.id, aliases.get(candidate.job_id and candidate.job_id.id or 0, False)) for candidate in candidates)
    
class HrJob(models.Model):
    _inherit = "hr.job"

    stage_ids = fields.Many2many(
        'hr.recruitment.stage', 'job_stage_rel', 'job_id', 'stage_id',
        'Job Stages', default=False)
    refer_candidate_count = fields.Integer(compute='_compute_refer_candidate_count', string="Refer Candidate")
    
    refer_candidate_count = fields.Integer(compute='_compute_refer_candidate_count', string="Refer Candidate")
    
    @api.multi
    def _compute_refer_candidate_count(self):
        job_candidate_srch = self.env['job.candidate'].search([('job_id', '=', self.id)])
        if job_candidate_srch:
            self.refer_candidate_count = len(job_candidate_srch)

    @api.multi
    def action_refer_candidate(self):
        hr_employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        return {
                'name' : 'Refer Candidate',
                'res_model' : 'job.candidate',
                'type' : 'ir.actions.act_window',
                'view_type' : 'form',
                'view_mode' : 'tree,form',
                'domain' : [('job_id', '=', self.id)],
                'context' : {
                             'default_job_id' : self.id,
                             'default_emp_id' : hr_employee.id,
                            }
        }
        
class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    is_last_stage = fields.Boolean('Is Last Stage', help="The application has reached in last stage")
    work_email = fields.Char('Work email', help="New email ID if applicant is employee")
    joining_date = fields.Date('Joining Date', help='Date the employee joined with company')

    @api.multi
    def check_if_last_stage(self, stage_id, job_id):
        self._cr.execute("select stage_id from job_stage_rel where job_id = %s", (job_id.id,))
        stage_list = []
        for each_stage_id in self._cr.fetchall():
            stage_list.append(each_stage_id[0])
        stage_brw = self.env['hr.recruitment.stage'].browse(stage_list)
        given_stage_brw = self.env['hr.recruitment.stage'].browse(stage_id)
        stage_list = []
        for each_stage in stage_brw:
            stage_list.append(each_stage.sequence)
        if given_stage_brw.sequence == max(stage_list):
            return 1
        return 0

    @api.multi
    def write(self, vals):
        res = super(HrApplicant, self).write(vals)
        if vals.has_key('stage_id'):
            if self.check_if_last_stage(vals['stage_id'], self.job_id):
                self.is_last_stage = True
            else:
                self.is_last_stage = False
        return res

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            address_id = contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({'name': applicant.partner_name or contact_name,
                                                           'job_id': applicant.job_id.id,
                                                           'address_home_id': address_id,
                                                           'department_id': applicant.department_id.id or False,
                                                           'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                                                           'work_email': applicant.work_email or False,
                                                           'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                employee._broadcast_welcome()
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window
