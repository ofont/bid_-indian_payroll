from openerp import models, fields, api, _
import datetime
from openerp import SUPERUSER_ID
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class hr_holidays_status(models.Model):
    _name = "hr.leave.type"
    _inherit = 'hr.leave.type'
    
    name = fields.Char('Leave Type', size=128)
    leaves = fields.Float("Total No Of Leaves", help="No of leave based on days and weeks")
    note = fields.Text("Specifications")
    interval_unit = fields.Selection([('days', 'Days'), ('weeks', 'Weeks')], 'Interval Unit')
    is_paid = fields.Boolean("Is Paid", help="Check if the assigned leaves are paid.")
    require_attachment = fields.Boolean("Requires Attachment")
    allow_carry_forward = fields.Boolean("Allow Carry Forward")
    allow_encashment = fields.Boolean("Allow Encashment")
    allow_half_days = fields.Boolean("Allow Half Days")
    earn_quaterly = fields.Boolean('Earn Quaterly')
    earn_yearly = fields.Boolean('Earn Yearly')
    allow_to_take_in_range = fields.Integer('Allow to take in range Of')
    use_within_months = fields.Integer('Use Within Months')
    number_of_leaves_to_earn_quaterly = fields.Integer('Leaves to Earn Quaterly')
    notify_before_elapse = fields.Boolean('Notify Before Elapse')
    notify_before_number_of_days = fields.Integer('Notify Before Number of Days')
    
    _defaults = {
               'interval_unit' : lambda *a: 'days',
               'leaves' : 0,
               }
    
class HrEmployeeCategory(models.Model):
    _inherit = "hr.employee.category"
    
    categ_leaves_ids = fields.One2many('hr.category.leaves', 'emp_categ_id', 'Add Leave Types')
    
class HrCategoryLeaves(models.Model):
    _name = "hr.category.leaves"
    
    emp_categ_id = fields.Many2one('hr.employee.category', 'Employee Category')
    leave_type = fields.Many2one('hr.leave.type', 'Leave Type')
    
class HrHolidays(models.Model):
    _inherit = "hr.leave"
    
    state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'), ('confirm', 'To Approve'), ('refuse', 'Refused'), ('validate1', 'Second Approval'), ('validate', 'Approved')],
            'Status', readonly=True, track_visibility='onchange', copy=False,
            help='The status is set to \'To Submit\', when a holiday request is created.\
            \nThe status is \'To Approve\', when holiday request is confirmed by user.\
            \nThe status is \'Refused\', when holiday request is refused by manager.\
            \nThe status is \'Approved\', when holiday request is approved by manager.', default='draft')
    notify = fields.Boolean('Notify with mail',default=False)
    half_day = fields.Boolean('Half Day')
    flag = fields.Boolean('Flag',default=True)
    evaluation_from_date = fields.Date('Evaluate From Date')
    evaluation_to_date = fields.Date('Evaluation To Date')
    evaluation_date_flag = fields.Boolean('Evaluation Date Field',readonly=True)
    
    
    @api.multi
    def holidays_first_validate(self):
        if self._uid == self.create_uid.id and self._uid != SUPERUSER_ID and self.employee_id.user_id.id == self._uid:
            return
        res = super(HrHolidays,self).holidays_first_validate()
        if not self.notify:
            return res
        if self.notify:
            if self.type == "remove":
                #Sending approval mail to hr
                hr_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_request_to_hr_remove")
                self.env['mail.template'].browse(hr_template_id.id).send_mail([each.id for each in self], force_send=True)
    #             sub_hr_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_sub_hr_remove")
    #             self.pool.get('mail.template').send_mail(self._cr, self._uid, sub_hr_template_id.id, [each.id for each in self], force_send=True)
            elif not self.holiday_status_id.double_validation:
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_approved_to_emp_add")
                self.env['mail.template'].browse(template_id.id).send_mail([each.id for each in self], force_send=True)
            elif self.holiday_status_id.double_validation:
                #Sending approval mail to hr
                hr_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_hr_add")
                self.env['mail.template'].browse(hr_template_id.id).send_mail([each.id for each in self], force_send=True)
    #             sub_hr_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_approved_to_sub_hr_add")
    #             self.pool.get('mail.template').send_mail(self._cr, self._uid, sub_hr_template_id.id, [each.id for each in self], force_send=True)
        return res
    
    @api.multi
    def holidays_validate(self):
#         print("\n self----------------->>>>>Holiday Validates",self)
        if self._uid == self.create_uid.id and self._uid != SUPERUSER_ID and self.employee_id.user_id.id == self._uid:
            return
        res = super(HrHolidays,self).holidays_validate()
        if not self.notify:
            return res
        if self.notify:
            if self.type == "remove":
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_hr_remove")
                emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_emp_remove")
    #             template_id.attachment_ids = None
    #             if self.employee_id.hr_id:
    #                 self.pool.get('mail.template').send_mail(self._cr, self._uid, template_id.id, [each.id for each in self], force_send=True)
                self.env['mail.template'].browse(emp_template_id.id).send_mail([each.id for each in self], force_send=True)
            else:
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_approved_to_emp_add")
                self.env['mail.template'].browse(template_id.id).send_mail([each.id for each in self], force_send=True)
        return res
    
    @api.model
    def create(self, vals):
#         print("----------------create leave ------------>>>>:::",self,vals)
        create_id = super(HrHolidays, self).create(vals)
#         print("----------------create leave ------------>>>>:::",self,vals,create_id)
        if create_id.holiday_status_id.use_within_months and create_id.evaluation_from_date and create_id.evaluation_to_date:
                if datetime.datetime.strptime(create_id.evaluation_to_date,'%Y-%m-%d') == datetime.datetime.strptime(create_id.evaluation_from_date,'%Y-%m-%d'):
                    create_id.number_of_days_temp = 1
                else:
                    create_id.number_of_days_temp = (datetime.datetime.strptime(create_id.evaluation_to_date,'%Y-%m-%d').date() - datetime.datetime.strptime(create_id.evaluation_from_date,'%Y-%m-%d').date()).days
                if create_id.number_of_days_temp < 0:
                    raise UserError(_('From Date Must be less than To Date'))
        return create_id
    
    @api.multi
    def write(self, vals):
#         print("\n validation--------------------->>>>self",self,self.validation_type)
        if len(self) == 1:
#             if self.type!="add":
                res = super(HrHolidays, self).write(vals)
                if self.holiday_status_id.allow_to_take_in_range > 0:
                    if self.number_of_days_temp < self.holiday_status_id.allow_to_take_in_range:
                        raise UserError(_('%s Leave Not Allowed to take less than %s')
                                % (self.holiday_status_id.name,self.holiday_status_id.allow_to_take_in_range))
                return res
        return super(HrHolidays, self).write(vals)
    
#     
    def _check_state_access_right(self, vals):
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not self.env['res.users'].has_group('base.group_sub_manager_user'):
            return False
        return True
    
    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        if self.holiday_status_id:
            if not self.holiday_status_id.allow_half_days:
                self.half_day = False
                self.flag = True
            else:
                self.flag = False
            if self.holiday_status_id.use_within_months > 0:
                self.evaluation_date_flag = True
            else:
                self.evaluation_date_flag = False
    
    @api.onchange('evaluation_from_date','evaluation_to_date')
    def onchange_evaluation_dates(self):
        if self.evaluation_from_date and self.evaluation_to_date:
            if datetime.datetime.strptime(self.evaluation_to_date,'%Y-%m-%d') == datetime.datetime.strptime(self.evaluation_from_date,'%Y-%m-%d'):
                self.number_of_days_temp = 1
            else:
                self.number_of_days_temp = (datetime.datetime.strptime(self.evaluation_to_date,'%Y-%m-%d').date() - datetime.datetime.strptime(self.evaluation_from_date,'%Y-%m-%d').date()).days
            if self.number_of_days_temp < 0:
                raise UserError(_('From Date Must be less than To Date'))
                    
    @api.model
    def refresh_emp_holidays(self):
        _logger.info('Leave Scheduler Started')
        current_date = datetime.datetime.now().date()
        holiday_status_obj = self.env['hr.leave.type']
        
        #Check For any leaves that are Getting Elapsed
#         non_carry_forward_leave_types = self.search([('allow_carry_forward','=',False),('notify_before_elapse','=',True)])
#         for each_leave_type in non_carry_forward_leave_types:
#             non_carry_forward_leaves = self.search([('holiday_status_id','=',each_leave_type.id)])
#             for each_non_carry_forward_leave in non_carry_forward_leaves:
#                 print'eeeeeeeeeeeee',each_non_carry_forward_leave
#                 if datetime.datetime.strptime(each_non_carry_forward_leave.evaluation_to_date.split(' ')[0], '%Y-%m-%d').date():
#                     pass
        
        #Leaves Refresh
        if current_date.month == 1 and current_date.day == 1:
            _logger.info('New Year Started')
            all_lapse_leave_types = self.env['hr.leave.type'].search([('allow_carry_forward','=',False)])
            all_lapse_leave_types = [each.id for each in all_lapse_leave_types]
            all_lapse_leaves = self.search([('type','=','add'),('holiday_status_id','in',all_lapse_leave_types)])
            all_lapse_leaves.holidays_reset()
            
            #Allocate leaves from new year(Casual and Sick Leaves)
            leaves_to_allocate_yearly = self.env['hr.leave.type'].search([('earn_yearly','=',True)])
            for each_leave in leaves_to_allocate_yearly:
                categ_lines = self.env['hr.category.leaves'].search([('leave_type','=',each_leave.id)])
                for each_line in categ_lines:
                    values = {
                          'holiday_status_id':each_leave.id,
                          'holiday_type':'category',
                          'category_id':each_line.emp_categ_id.id,
                          'number_of_days_temp':each_leave.leaves,
                          'type':'add',
                          'notify':False
                          }
                    created_id = self.with_context().create(values)
                    
        if current_date.day == 1:
            _logger.info('New Month Started')
            #JUST A NEW MONTH
            pass
        if (current_date.month)%3 == 1 and current_date.day == 1:
            _logger.info('New Quarter Started')
            leaves_earned_quaterly = holiday_status_obj.search([('earn_quaterly','=',True)])
            for each_leave in leaves_earned_quaterly:
                categ_lines = self.env['hr.category.leaves'].search([('leave_type','=',each_leave.id)])
                for each_line in categ_lines:
                    values = {
                          'holiday_status_id':each_leave.id,
                          'holiday_type':'category',
                          'category_id':each_line.emp_categ_id.id,
                          'number_of_days_temp':each_leave.number_of_leaves_to_earn_quaterly,
                          'type':'add',
                          'notify':False
                          }
                    created_id = self.with_context().create(values)
                    
        #Elapse Leaves that are to be elapsed in between year ends
        leaves_to_end_with_in = holiday_status_obj.search([('use_within_months','>',0)])
        _logger.info('Leaves to end (%s)', (leaves_to_end_with_in,))
        for each_leave in leaves_to_end_with_in:
            check_for_leaves = self.search([('type','=','add'),('holiday_status_id','=',each_leave.id),('state','=','validate')])
            for each_hr_holiday in check_for_leaves:
                evaluation_from_date = datetime.datetime.strptime(each_hr_holiday.evaluation_from_date.split(' ')[0], '%Y-%m-%d').date()
                evaluation_to_date = datetime.datetime.strptime(each_hr_holiday.evaluation_to_date.split(' ')[0], '%Y-%m-%d').date()
                current_date = datetime.datetime.now().date()
                if current_date > (evaluation_to_date + relativedelta(months=each_leave.use_within_months)):
                    each_hr_holiday.holidays_reset()
                else:
                    #DO NOT RESET AS WITHIN PERIOD
                    #Sending mail before n days of elapse
                    if current_date == (evaluation_to_date + relativedelta(months=each_leave.use_within_months) - relativedelta(days=each_leave.notify_before_number_of_days)):
                        #Leave will elapse after 10 days
                        template_id = self.env['ir.model.data'].get_object('indian_payroll', "inform_leave_elapse")
                        self.env['mail.template'].browse(template_id.id).send_mail([each.id for each in self], force_send=True)
                            
                            
        _logger.info('Leave Scheduler Completed')
    @api.multi
    def holidays_refuse(self):
        print("\n self----------------->>>>>Holiday refuse",self)
        if self._uid == self.create_uid.id and self._uid != SUPERUSER_ID and self.employee_id.user_id.id == self._uid:
            return
        res = super(HrHolidays,self).holidays_refuse()
        template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_rejected_to_emp_add")
        
        return res
    
    @api.multi
    def validate(self):
#         print("\n self----------------->>>>>holidays_confirm refuse",self)
        self.write({
        'state': 'validate',
            })
        res = super(HrHolidays,self).validate()
        if self._uid == self.employee_id.user_id.id:
            self.notify = True
        if self.type == "add":
            is_hr = self.env['res.users'].has_group('hr.group_hr_user')
            if is_hr and self.employee_id.user_id.id != self._uid or self._uid == SUPERUSER_ID:
                #Send no Mail
                pass
            else:
                if self.holiday_status_id.double_validation:
                    template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_manager_add")
                    template_id.attachment_ids = None
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
                else:
                    template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_hr_add")
                    template_id.attachment_ids = None
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
                emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_emp_add")            
                self.env['mail.template'].browse(emp_template_id.id).send_mail(self.id, force_send=True)
        else:
            if self.holiday_status_id.require_attachment:
                #check attachment
                ir_attachment_obj = self.env['ir.attachment'].search([('res_id', '=', self.id)])
                if not ir_attachment_obj:
                    raise UserError(_('Attachment required for this leave'))
            if not self.holiday_status_id.double_validation:
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_request_to_hr_remove")
                template_id.attachment_ids = None
                if self.employee_id.hr_id:
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
            else:
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_request_to_sub_hr_remove")
                template_id.attachment_ids = None
                self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
            emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_request_to_emp_remove")            
            self.env['mail.template'].browse(emp_template_id.id).send_mail(self.id, force_send=True)
        return res
    
class MailMail(models.Model):
    _inherit = "mail.mail"
    
    @api.model
    def create(self, values):
        if not 'body_html' in values:
            for each in values:
                if 'body_html' in values[each]:
                    values = values[each]
                    return super(MailMail, self).create(values)
        else:
            if 'itemscope' in values.get('body_html'):
                return self
            return super(MailMail, self).create(values)
    
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee and employee.user_id:
            self.message_subscribe_users(user_ids=[employee.user_id.id])