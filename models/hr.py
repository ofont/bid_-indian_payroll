import logging
from openerp.api import multi
from pkg_resources import require

_logger = logging.getLogger(__name__)

import calendar
import time
import math
import fnmatch
import os
# from datetime import datetime
import pytz
import glob
import csv
from xlrd import open_workbook
from openerp import tools
import datetime as DateTime
# from datetime import date, timedelta
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
# from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import UserError, Warning
from openerp import api, fields, models, _
from dateutil import parser
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID

class ResUsers(models.Model):
    _inherit = "res.users"
    
    emp_id = fields.Many2one('hr.employee', 'Employee ID')


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    groups_id = fields.Many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', string='Groups')
    create_user = fields.Boolean('Create Login User', default=True)
    work_email = fields.Char('Work Email', size=240, required=True, readonly=True)
    work_location = fields.Char('Work Location', readonly=True)
    asset_product_ids = fields.One2many('asset.product.line', 'hr_id', string='Asset Products')
    contract_type = fields.Selection([
        ('full_time_contractor', 'Full-time contractor'),
        ('part_time_contractor', 'Part-time contractor'),
        ('fixed_term_contracts', 'Fixed-term contracts'),
        ('agency_staff', 'Agency Staff'),
        ('freelancers', 'Freelancers'),
        ('zero_hour_contracts', 'Zero Hour contracts')], 'Contract types')
    employee_attach_ids = fields.One2many('ir.attachment', 'emp_attach_id', 'Employee Attachment')
    user_id = fields.Many2one('res.users', 'Salesperson', help='The internal user that is in charge of communicating with this contact if any.',                          )
    job_id = fields.Many2one('hr.job', 'Job Title', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    notification_id = fields.Many2one('notification.message', 'Message')
    parent_id = fields.Many2one('hr.employee', 'Manager')
    children_ids = fields.One2many('hr.employee', 'parent_id', 'Childrens')
    address_home_id = fields.Many2one('res.partner', 'Home Address', readonly=True)
    related_customer = fields.Many2many('res.partner', 'employee_customer_rel', 'emp_id', 'partner_id', 'Related Customer', ondelete='cascade')
    #     related_customer = fields.Many2one('res.partner', 'Related Customer')
    related_vendor = fields.Many2many('res.partner', 'employee_vendor_rel', 'emp_id', 'partner_id', 'Related Vendor', ondelete='cascade')
    #     related_vendor = fields.Many2one('res.partner', 'Related Vendor')
    code = fields.Char('Employee Code', default=0, required=True, readonly=True)
    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account Number', readonly=True, domain="[('partner_id','=',address_home_id)]", help="Employee bank salary account")
        
    joining_date = fields.Date('Joining Date', help='Date the employee joined with company', readonly=True)
#     offered_amount = fields.Float('Offered Amount', readonly=True)
    hr_id = fields.Many2one('hr.employee', 'HR')
    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', 'Tags', required=True)
    leave_type_ids = fields.Many2many('hr.leave.type', 'emp_comp_st', 'emp_id', 'st_id' , 'Leave Types', states={'active':[('readonly', True)], 'terminated':[('readonly', True)], 'draft1':[('readonly', True)]})
    
    _sql_constraints = [
        ('email_uniq', 'unique(work_email)', 'Email Id has to be unique.'),
        ('code_uniq', 'unique(code)', 'Employee Code has to be unique.')
    ]
    
    @api.model
    def create(self, vals):
        print ("In createeeeeee    ",self)
        '''
            create a res login user on employee creation
        '''
        hr_id = super(HrEmployee, self).create(vals)
        HrHolidaysObj = self.env['hr.leave']
        print("\n hr leave----------->>>",HrHolidaysObj)
        if hr_id.category_ids:
            for each_emp_categ in hr_id.category_ids:
                for each_leave_type in each_emp_categ.categ_leaves_ids:
                    hrHoliday = HrHolidaysObj.create({'employee_id': hr_id.id, 'holiday_type': 'employee', 'number_of_days_temp': each_leave_type.leave_type.leaves, 'holiday_status_id': each_leave_type.leave_type.id, 'type': 'add'})
                    hrHoliday.state = 'validate'
        
        if hr_id.create_user:
#             print("\n user id----------->>>hr_id-----",hr_id.create_user)
            my_employees_action_id = self.env['ir.model.data'].get_object_reference('indian_payroll', 'open_view_employee_list_my_inherit')
#             print("\n action id as---1111----------->>>>>",my_employees_action_id)
#             my_employees_action_id = self.env.ref('indian_payroll', 'open_view_employee_list_my_inherit')
            res_user_id = self.env['res.users'].create(
                {'emp_id': hr_id.id, 'name': vals.get('name'), 'login': vals.get('work_email'), 'action_id': my_employees_action_id[1]})
            vals['address_home_id'] = res_user_id.partner_id.id
            res_user_id.partner_id.email = vals.get('work_email')
            print("\n ----res_user_id-----+++++++",res_user_id)
            res_user_id.action_reset_password()
            # set hr for emp
            
            groups_obj = self.env.ref("hr.group_hr_user").users
            groups_obj1=self.env['res.groups'].search([('name','=','My Employee')])
            groups_obj2=self.env['res.groups'].search([('name','=','Internal User')])
#             print("\n groups_obj+++++++++++++++++++++++++++",groups_obj1,groups_obj2)
            
            hr = False
            if groups_obj:
                for each_hr in groups_obj:
                    if each_hr.emp_id:
                        hr = each_hr.emp_id.id
#                         print("\n hr---------------->>>>",hr)
                        break
            hr_id.write({'user_id': res_user_id.id, 'address_home_id': res_user_id.partner_id.id, 'hr_id':hr,'groups_id':[(6, 0, [])]})
        print('last',hr_id.category_ids)
#         print("\n action id as-------------->>>>>",hr_id.user_id)
        if groups_obj1:
                write_id=hr_id.user_id.write({'groups_id':[(6, 0, [groups_obj1.id,groups_obj2.id])]})
#                 print('lastWWWWWWWWWWWWW',hr_id.category_ids,write_id)
        return hr_id
    
    @api.multi
    def write(self, vals):
        categ_list_ids = []
        for categ in self.category_ids:
            categ_list_ids.append(categ.id)
        HrHolidaysObj = self.env['hr.leave']
        if 'category_ids' in vals:
            del_categ_list1 = set(categ_list_ids) - set(vals['category_ids'][0][2])
            #print "Del 11 ",del_categ_list1
            del_categ_list2 = set(vals['category_ids'][0][2]) - set(categ_list_ids)
            #print "Del 22 ",del_categ_list2
            if del_categ_list1:
                for categ in del_categ_list1:
                    brw_categ = self.env['hr.employee.category'].browse(categ)
                    for unlink_cat in brw_categ.categ_leaves_ids:
                        available_holidays = HrHolidaysObj.search([('employee_id','=',self.id),('holiday_type','=','employee'),('holiday_status_id','=',unlink_cat.leave_type.id)])
                        if available_holidays:
                            available_holidays.state = 'cancel'
                            available_holidays.unlink()
                        
            if del_categ_list2:
                for categ in del_categ_list2:
                    brw_categ = self.env['hr.employee.category'].browse(categ)
                    for unlink_cat in brw_categ.categ_leaves_ids:
                        available_holidays = HrHolidaysObj.search([('employee_id','=',self.id),('holiday_type','=','employee'),('holiday_status_id','=',unlink_cat.leave_type.id)])
                        if available_holidays:
                            available_holidays.state = 'cancel'
                            available_holidays.unlink()
            for each_emp_categ in vals['category_ids'][0][2]:
                categ_id = self.env['hr.employee.category'].browse(each_emp_categ)
                for each_leave_type in categ_id.categ_leaves_ids:
                    holidays = HrHolidaysObj.search([('employee_id','=',self.id),('holiday_type','=','employee'),('number_of_days_temp','=', each_leave_type.leave_type.leaves)])
                    if not holidays:
                        hrHoliday = HrHolidaysObj.create({'employee_id': self.id, 'holiday_type': 'employee', 'number_of_days_temp': each_leave_type.leave_type.leaves, 'holiday_status_id': each_leave_type.leave_type.id, 'type': 'add'})
                        hrHoliday.state = 'validate'
            
        res= models.Model.write(self, vals)
        return res
                        
    @api.model
    def get_hr_email_id(self):
        groups_obj = self.env.ref("hr.group_hr_user").users
        for each_hr in groups_obj:
            if each_hr.emp_id:
                emp_id = each_hr.emp_id[0]
                return emp_id.work_email
    
    @api.multi
    def calculate_expense(self, date_from, date_to):
        """
        Calculate total expense amount for employee and return it.
        """
        expense_ids = self.env['hr.expense'].search(
            [('include_in_payslip', '=', True), ('payment_mode', '=', 'own_account'), ('employee_id', '=', self.id), ('date', '<=', date_to),
             ('date', '>=', date_from)])
        total_expense = 0
        points_achieved_after_completion = 0
        total_points_amount = 0
        target_task_complete_ids = self.env['target.tasks'].search([('completed_by', '=', self.id)])
        for item in target_task_complete_ids:
            points_achieved_after_completion += item.points_achieved
        res = self.env['settings.settings'].default_get(['point_achieved_amount'])
        if 'point_achieved_amount' in res and res['point_achieved_amount']:
            total_points_amount = points_achieved_after_completion * float(res['point_achieved_amount'])
        for each_expense_id in expense_ids:
            total_expense += each_expense_id.total_amount
        total_expense += total_points_amount
        return total_expense

    @api.model
    def get_user_email_id(self):
        emp_id = self.env['hr.employee'].search([('user_id','=',self._uid)])
        if emp_id:
            emp_id = emp_id[0]
            return emp_id.work_email
