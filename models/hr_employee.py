from openerp import api, fields, models, _
from datetime import date,datetime
from openerp.exceptions import UserError,ValidationError,Warning
from openerp import SUPERUSER_ID


class hr_employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
#     uid = fields.Many2one('res.users', 'User', required=True, readonly=True,
#                               default=lambda self: self.env.uid)
#     employee_auto_id = fields.Char('Employee ID', default=lambda obj:
#         obj.env['ir.sequence'].next_by_code('hr.employee'))
    universal_account_number = fields.Char(string='UAN', help='Universal account number')
    permanent_account_number = fields.Char(string='PAN', help='Permanent account number')
    pf_number = fields.Char(string="PF Number");
    base_branch = fields.Char(string="Base Branch")
    employee_age = fields.Char(string="Age", store=True)
    financial_year_ids=fields.One2many('declaration.financial.year','employee_id','Financial Year')
    is_employee = fields.Boolean('is_employee', default=True)  
    work_phone = fields.Char('Work Phone')
    mobile_phone = fields.Char('Work Mobile')
    parent_id = fields.Many2one('hr.employee', 'Manager')
    address_home_id = fields.Many2one('res.partner', 'Home Address')
    coach_id = fields.Many2one('hr.employee', 'Coach')
    country_id = fields.Many2one('res.country', 'Nationality (Country)')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], 'Gender')
    marital = fields.Selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Marital Status')
    birthday = fields.Date("Date of Birth")
    address_id = fields.Many2one('res.partner', 'Working Address')
    manager = fields.Boolean('Is a Manager')
    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', 'Tags')
    
    
    _sql_constraints = [
        ('employee_auto_id_uniq', 'unique(employee_auto_id)', 'Employee ID Number must be unique per Employee!'),
        ('universal_account_number_uniq', 'unique(universal_account_number)', ' Please enter Unique UAN id.'),
        ('permanent_account_number_uniq', 'unique(permanent_account_number)', ' Please enter Unique PAN id.'),
        ('pf_number_uniq', 'unique(pf_number)', ' Please enter Unique PF number.')
    ]
    
        
    @api.onchange('birthday')
    def onchange_birthday(self):
        if self.birthday:
            born_date = datetime.strptime(self.birthday, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - born_date.year - ((today.month, today.day) < (born_date.month, born_date.day))
            self.employee_age = age
        else:
            print ("--")
            
            
    @api.model
    def send_birthday_email(self):
        template = self.env.ref('indian_payroll.email_template_birthday_wish')
        channel_id = self.env['ir.model.data'].get_object_reference('indian_payroll', 'channel_birthday')[1]
        today = datetime.now()
        today_month_day = '%-' + today.strftime('%m') + '-' + today.strftime('%d')
        employee_ids = self.search([('birthday', 'like', today_month_day)])
        employees = self.search([])
        persons = []
        if employee_ids:
            for birthday in employee_ids:
                persons.append(birthday.name)
            main_body_html = template.body_html
            print( "Length   ",len(persons),persons)
            
            if len(persons) == 1:
                person = persons[0]
            elif len(persons) >= 1 and len(persons) <= 2:
                person = persons[0] + ' & ' + persons[1]
            else:
                person = ", ".join(persons[0:-1])
                person = person + ' & ' + persons[-1]
            body_html = "Dear, "+ person + "<br />" + template.body_html
            template.write({'body_html': body_html})
            for employee in employees:
#                 res = self.env['mail.channel'].browse([channel_id]).message_post(body=_('Happy Birthday Dear %s.') % (employee.name), partner_ids=[employee.id])
#                 print "RESSSS   ",res
                
                employee.message_post_with_template(template.id,composition_mode='comment')
            template.write({'body_html': main_body_html})
        return None
#     @api.model
#     def create(self, vals):
#         item_ids=self.search([('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start)])
#         if item_ids:
#             raise Warning(_('Invalid Date range!'))
#         return models.Model.create(self, vals)
    
#     @api.multi
#     def write(self, vals):
#         res= models.Model.write(self, vals)
#         print "Valsssssssssssssss   ",vals
#         print self.financial_year_ids
#         for config in self.env['declaration.configuration'].search([]):
#             declaration_obj=self.env['declaration.financial.year'].search([('financial_year_id','=',config.financial_year_id.id)])
#             print "Declaration objeeeeeeeeee  ",declaration_obj
#             for declaration in declaration_obj:
#                 if config.locking_date<=str(datetime.now().date()):
#                     raise Warning(_('You are not allowed to update declarations...! Please contact your department'))
#                     print "Truuuuuuuuueeeeeeeeeeeeeee ",config.locking_date
#                 else:
#                     print "Faaaaaaaaaaaaaaalseeeeeeeeeeeee ",config.locking_date
#         return res
