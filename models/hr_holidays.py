from odoo import api, fields, models, _

class hr_holiday(models.Model):
    _inherit = 'hr.leave'
    
    @api.model
    def default_get(self, fields):
        res = super(hr_holiday, self).default_get(fields)
        context = dict(self._context or {})
        #print "Context   ",context
        active_id = self.env.context.get('active_id')
        if active_id:
            res['employee_id'] = context['employee_id']
            res['state'] = 'confirm'
        return res
    @api.model
    def create(self,vals):
        return super(hr_holiday,self).create(vals)
    
    @api.multi
    def action_confirm(self):
#         print ("in the ction confirmssssss-------------------",self)
        res = super(hr_holiday,self).action_confirm()
#         print('\n ction confirmssssss self id------------->>::::::::::::',self.employee_id.user_id.id,self._uid)
        if self._uid == self.employee_id.user_id.id:
            
            self.notify = True
            is_hr = self.env['res.users'].has_group('hr.group_hr_user')
#             print("\n hr-----<<<<<<<<<<<<<<<",is_hr)
            if is_hr and self.employee_id.user_id.id != self._uid:
                #Send no Mail
                pass
            else:
                if self.holiday_status_id:
#                     print("\n hr-elssss----<<<<<<<<<<<<<<<",is_hr)
                    template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_manager_add")
                    template_id.attachment_ids = None
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
                else:
                    template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_hr_add")
                    template_id.attachment_ids = None
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
        emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_request_to_emp_add")            
        self.env['mail.template'].browse(emp_template_id.id).send_mail(self.id, force_send=True)
        return res
     
    @api.multi    
    def action_refuse(self):
#         print ("in the action_refuse buttonnnnnn-------------------",self._uid,self.create_uid.id,self.employee_id.user_id.id)
        if self:
            if self._uid == self.create_uid.id and self._uid != self.employee_id.user_id.id == self._uid:
                return
            res = super(hr_holiday,self).action_refuse()
            template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_rejected_to_emp_add")
            template_id.attachment_ids = None
            self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
#             print("-------------Res in action refuses-------------->>>>>",template_id)
            self.state='confirm'
            return res
    @api.multi    
    def action_approve(self):
#         print ("in the actionapproval--- buttonnnnnn-------------------",self._uid,self.create_uid.id,self.employee_id.user_id.id)
        if self:
            if self._uid == self.create_uid.id and self._uid != self.employee_id.user_id.id == self._uid:
                return
            res = super(hr_holiday,self).action_refuse()
            template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_emp_remove")
            template_id.attachment_ids = None
            self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
#             print("-------------Res in approval-------------->>>>>",template_id)
            self.state='validate'
            return res
    @api.multi    
    def action_validate(self):
        print ("in the action_validate buttonnnnnn-------------------",self)
#         print('\n sale of notify----------------->>>>',self.notify)
        res = super(hr_holiday,self).action_validate()
        if not self.notify:
            return res
        if self.notify:
#                 print('\n sale of notify----------------->>>>',self.notify)
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_hr_remove")
                emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_approved_to_emp_remove")
                self.env['mail.template'].browse(emp_template_id.id).send_mail([each.id for each in self], force_send=True)
        else:
                template_id = self.env['ir.model.data'].get_object('indian_payroll', "leave_allocation_approved_to_emp_add")
                self.env['mail.template'].browse(template_id.id).send_mail([each.id for each in self], force_send=True)
#         print("\n in the last reeeeeeeeeeeeeee",res)
        return res
    @api.multi    
    def second_validate(self):
        print ("in the second_validate buttonnnnnn-------------------",self)
     
        
    