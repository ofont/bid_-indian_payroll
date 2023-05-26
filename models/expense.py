from openerp import api, fields, models, _
from datetime import datetime
from openerp.exceptions import UserError
import openerp.addons.decimal_precision as dp

class ExpenseCategory(models.Model):
    _name = "expense.category"
    
    name = fields.Char('Name',required=True)
    
class HrExpense(models.Model):
    _inherit = "hr.expense"
    include_in_payslip = fields.Boolean('Include in Payslip')

    unit_amount = fields.Float(string='Total Cost Incurred', readonly=True, required=True, states={'draft': [('readonly', False)]},
                               digits=dp.get_precision('Product Price'))
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project',
                                          states={'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account',
                                          domain=[('account_type', '=', 'normal')])
    category_id = fields.Many2one('expense.category', 'Category')
    receipt_invoice_number = fields.Char('Receipt/Invoice Number')
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)],required=False)
    description = fields.Text(required=True)
    
    @api.multi
    def date_check(self):
        fmt = '%Y-%m-%d'
        current_date = (datetime.today()).strftime(fmt)
        d1 = datetime.strptime(str(self.date), fmt)
        d2 = datetime.strptime(str(current_date), fmt)
        daysDiff = (d2 - d1).days
        if daysDiff > 90:
            raise UserError('Date Cannot Exceed more than 3 Months!!')

    @api.model
    def create(self, vals):
        res = super(HrExpense, self).create(vals)
        fmt = '%Y-%m-%d'
        current_date = (datetime.today()).strftime(fmt)
        d1 = datetime.strptime(str(res.date), fmt)
        d2 = datetime.strptime(str(current_date), fmt)
        daysDiff = (d2 - d1).days
        if daysDiff > 90:
            raise UserError('Date Cannot Exceed more than 3 Months!!')
        return res

    @api.multi
    def write(self, vals):
        res = super(HrExpense, self).write(vals)
        fmt = '%Y-%m-%d'
        current_date = (datetime.today()).strftime(fmt)
        print("\n current date --and self .date",current_date,self.date)
        if self.date:
            d1 = datetime.strptime(str(self.date), fmt)
            d2 = datetime.strptime(str(current_date), fmt)
            daysDiff = (d2 - d1).days
            if daysDiff > 90:
                raise UserError('Date Cannot Exceed more than 3 Months!!')
        return res
    
    @api.multi
    def submit_expenses(self):
        ir_attachment_obj = self.env['ir.attachment'].search([('res_id', '=', self.id)])
        if not ir_attachment_obj:
            raise UserError('No Document Attached!!')
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You can only submit draft expenses!"))
        groups_obj = self.env.ref("hr.group_hr_user").users
        template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_hr_expense")
        emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_emp_expense")
        template_id.attachment_ids = None
        for attachment_obj in ir_attachment_obj:
            if attachment_obj.id:
                template_id.attachment_ids = [attachment_obj.id]
        for i in groups_obj:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', i.id)])
            if hr_employee:
                if hr_employee.work_email:
                    self.hr_manager_email_id = hr_employee.work_email
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
#         self.pool.get('mail.template').send_mail(self._cr, self._uid, emp_template_id.id, self.id, force_send=True)
        self.state = 'reported'
    
    @api.multi
    def approve_expenses(self):
        ir_attachment_obj = self.env['ir.attachment'].search([('res_id', '=', self.id)])
        groups_obj = self.env.ref("hr.group_hr_user").users
        template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_hr_expense_approved")
        emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_emp_expense_approved")
        template_id.attachment_ids = None
        for attachment_obj in ir_attachment_obj:
            if attachment_obj.id:
                template_id.attachment_ids = [attachment_obj.id]
        for i in groups_obj:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', i.id)])
            if hr_employee:
                if hr_employee.work_email:
                    self.hr_manager_email_id = hr_employee.work_email
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
        self.env['mail.template'].browse(emp_template_id.id).send_mail(self.id, force_send=True)
        self.write({'state': 'approve'})

    @api.multi
    def refuse_expenses(self, reason):
        ir_attachment_obj = self.env['ir.attachment'].search([('res_id', '=', self.id)])
        groups_obj = self.env.ref("hr.group_hr_user").users
        template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_hr_expense_rejected")
        emp_template_id = self.env['ir.model.data'].get_object('indian_payroll', "email_template_emp_expense_rejected")
        template_id.attachment_ids = None
        for attachment_obj in ir_attachment_obj:
            if attachment_obj.id:
                template_id.attachment_ids = [attachment_obj.id]
        for i in groups_obj:
            hr_employee = self.env['hr.employee'].search([('user_id', '=', i.id)])
            if hr_employee:
                if hr_employee.work_email:
                    self.hr_manager_email_id = hr_employee.work_email
                    self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
        self.env['mail.template'].browse(emp_template_id.id).send_mail(self.id, force_send=True)
        self.write({'state': 'cancel'})
