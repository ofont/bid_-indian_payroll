from openerp import api, fields, models, _
import datetime
from operator import add
from datetime import datetime, date
from dateutil import relativedelta
import time
from openerp.exceptions import UserError,ValidationError,Warning
from openerp import api, tools
import math

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'
    
    total_income = fields.Float('Total Income', compute="get_total_income", store=True)
    total_prof_tax = fields.Float('Total PF', compute="get_total_professional_tax", store=True)
    taxable_income = fields.Float('Taxable Income', compute="get_taxable_income", store=True)
    yearly_tds = fields.Float('Yearly TDS', compute="get_yearly_tds", store=True)
    recovered_tds = fields.Float('Recovered TDS', compute="get_recovered_tds", store=True)
    total_declarations = fields.Float('Total Declaration', compute="get_total_declaration", store=True)
    ded_cat_list = []
    alw_cat_list = []
    
    
    row_list_right = []
    last_row_list_left = []
    row_list_left = []
    last_row_list_right = []
    
    @api.model
    @api.depends('contract_id')
    @api.onchange('employee_id', 'date_from', 'contract_id')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        employee_id = self.search([('employee_id', '=', self.employee_id.id),('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])
        if employee_id.state == 'draft' or employee_id.state == 'done':
            raise Warning(_('Payslip has been already generated for the selected month'))

        else:
        
            if self.contract_id:
#                 print("\n in contract id---------iffffffffffff->>>>>",self.contract_id)
                contract_start_date = datetime.strptime(str(self.contract_id.date_start) , '%Y-%m-%d').date()
                payslip_start_date = datetime.strptime(str(self.date_from) , '%Y-%m-%d').date()
                if contract_start_date.month == payslip_start_date.month:
                    date_from = contract_start_date.strftime('%Y-%m-%d')
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
            self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(str(ttyme.strftime('%B-%Y'))))
            self.company_id = employee.company_id
            contract_ids=0
#             print("\n self contract------------>>>>>",self.contract_id)
            if not self.env.context.get('contract') or not self.contract_id:
                contract_ids = self.get_contract(employee, date_from, date_to)
#                 print("\n contract id-------------->>>>>>:::::::::::::",contract_ids)
                if not contract_ids:
                    return
                self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
#                 print("\n if not contract id----------------->>>>>",self.contract_id)
            if not self.contract_id.struct_id:
                return
            self.struct_id = self.contract_id.struct_id
    
            # computation of the salary input
            worked_days_line_ids=0
            worked_days_line_ids = self.get_worked_day_lines(self.contract_id, date_from, date_to)
#             print("\n --------------------->>>>>",worked_days_line_ids)
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            self.worked_days_line_ids = worked_days_lines
    
            input_line_ids = self.get_inputs(self.contract_id, date_from, date_to)
            input_lines = self.input_line_ids.browse([])
            for r in input_line_ids:
                input_lines += input_lines.new(r)
            self.input_line_ids = input_lines
        return
    
    @api.multi
    @api.depends('line_ids', 'total_income', 'taxable_income')
    def get_yearly_tds(self):
        declarations = [dec.amount for year in self.employee_id.financial_year_ids for section in year.it_declaration_ids for dec in section.declaration_line_ids]
        taxable_income = round(self.total_income - sum(declarations))
        slab = self.env['it.slab'].search([('person_type', '=', self.employee_id.gender)], limit=1)
        slab_line = self.env['it.slab.line'].search([('from_amount', '<', taxable_income), ('to_amount', '>=', taxable_income), ('slab_id', '=', slab.id)], limit=1)
        tds1=0
        for line in slab.it_slab_line_ids:
            if taxable_income>=line.to_amount:
                tds1=tds1+line.estimated_tax
        tds2=(slab_line.tax_percent/100)*(taxable_income-slab_line.from_amount)
        self.yearly_tds = tds2+tds1
        
    @api.multi
    @api.depends('line_ids', 'total_income', 'taxable_income')
    def get_recovered_tds(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
        #print "Fin year ============== ", fin_year
        payslips = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '>', fin_year.date_start), ('state','=','draft'),('date_from', '<=', fin_year.date_end)])
        lst=[]
        lst = [line.total for payslip in payslips for line in payslip.line_ids if line.code == 'TDS']
        if lst:
            self.recovered_tds = round(sum(lst))
            
            fmt = '%Y-%m-%d'
            r = relativedelta.relativedelta(datetime.strptime(fin_year.date_end, fmt), datetime.strptime(self.date_to, fmt))   
            projected_tds = (self.yearly_tds - self.recovered_tds) / r.months  # self.contract_id.tds= 
            if projected_tds and self.contract_id.id:
                self._cr.execute('update hr_contract set tds=%s where id=%s', (projected_tds, self.contract_id.id))
        
        
    
    @api.multi
    @api.depends('line_ids', 'total_income')
    def get_taxable_income(self):
        declarations = [dec.amount for year in self.employee_id.financial_year_ids for section in year.it_declaration_ids for dec in section.declaration_line_ids]
        self.taxable_income = round(self.total_income - sum(declarations))
    
    @api.multi
    @api.depends('line_ids')
    def get_total_income(self):
        fmt = '%Y-%m-%d'
        actual_days_in_mnth = datetime.strptime(str(self.date_to), fmt) - datetime.strptime(str(self.date_from), fmt)
        paid_days = self.get_no_days_paid()
        gross_lst = [line.total for line in self.line_ids if line.code == 'GROSS']
        if gross_lst:
            actual = (gross_lst[0] / actual_days_in_mnth.days + 1) * paid_days
            fin_year = self.env['financial.year.master'].search([('date_start', '<', str(self.date_from)), ('date_end', '>', str(self.date_from))], limit=1)
            if fin_year:
                balance_months = relativedelta.relativedelta(datetime.strptime(fin_year.date_end, fmt), datetime.strptime(str(self.date_to), fmt))
                projected = gross_lst[0] * balance_months.months
    #             # print"fin_year------------------------",projected,gross_lst
                self.total_income = round(projected + actual)
            
    @api.multi
    @api.depends('line_ids')
    def get_total_professional_tax(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
        payslips = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '>', fin_year.date_start), ('date_from', '<=', fin_year.date_end)])
        for line in self.line_ids:
            if line.code == 'PTD':
                self.total_prof_tax = abs(line.amount) * 12
            if line.code == 'PT':
                self.total_prof_tax = abs(line.amount) * 12
        
        
    def get_current_date(self):
        date = ''
        if self.state == 'done':
            date = "Payslip generated on : " + self.write_date
        else:
            date = ' ----/--/--'
        return date
        
    @api.multi
    def apply_day_leave(self):
        view_id = self.env.ref(
           'hr_holidays.hr_leave_view_form').id
        context = dict(self._context or {})
        print("\n leave requiest as------------>>>>",view_id)
        context['employee_id'] = self.employee_id.id
#         context['department_id'] = self.employee_id.department_id.id
        context['state'] = 'validate'
        holidays_obj = self.env['hr.leave'];
        context['holiday_status_id'] = ''
        return {
                'name': 'Leaves Request',
               'view_type': 'form',
               'view_mode': 'form',
               'res_model': 'hr.leave',
#                'view_id': view_id,
               'type': 'ir.actions.act_window',
               'target': 'new',
               'context': context
        }
        
    def get_rows(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
        total_dec = 0
        dec_line = 0
        dicl_list = []
        for year in self.employee_id.financial_year_ids:
            for declaration in year.it_declaration_ids:
                total_dec = total_dec + 1
                for line in declaration.declaration_line_ids:
                    # print"Declaration name ",line.it_declaration_id
                    dec_line = dec_line + 1
                    dicl_list.append(line.it_declaration_id.name)
                    dicl_list.append(line.amount)
                    my_list = [dicl_list[i:i + 4] for i in range(0, len(dicl_list), 4)]
        total_rows = math.ceil(dec_line / 3)
        if total_rows == 0:
            total_rows = 1
        return total_rows
        
    def get_declaration_heads(self):
        dicl_list = []
        my_list = []
        dec_line = 0
        if self.employee_id.financial_year_ids:
            for year in self.employee_id.financial_year_ids:
                for declaration in year.it_declaration_ids:
                    for line in declaration.declaration_line_ids:
                        dec_line = dec_line + 1
                        dicl_list.append(line.it_declaration_id.name)
                        dicl_list.append(line.amount)
                        my_list = [dicl_list[i:i + 4] for i  in range(0, len(dicl_list), 4)]
        for i in range(len(my_list) % 4):
            my_list.append(' ')
            
        my_list = [dicl_list[i:i + 4] for i  in range(0, len(dicl_list), 4)]
        self.last_row_list_left = my_list
        return my_list
        
    def get_declaration(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
        total_dec = 0
        dec_line = 0
        for year in self.employee_id.financial_year_ids:
            for declaration in year.it_declaration_ids:
                total_dec = total_dec + 1
                for line in declaration.declaration_line_ids:
                    dec_line = dec_line + 1
        return dec_line
        
        
    @api.multi
    def get_no_leaves(self, type):
        leave_type = False
        if type == 'SL':
            leave_type = self.env['hr.leave.type'].search([('name', 'like', 'Sick')], limit=1)
        if type == 'EL':
            leave_type = self.env['hr.leave.type'].search([('name', 'like', 'Earned')], limit=1)
        if type == 'CL':
            leave_type = self.env['hr.leave.type'].search([('name', 'like', 'Casual')], limit=1)
        if type == 'VL':
            leave_type = self.env['hr.leave.type'].search([('name', 'like', 'Vacation')], limit=1)
        hr_hol_obj = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id), ('holiday_status_id', '=', leave_type.id)])
        lst = [line.number_of_days for line in hr_hol_obj]
        return sum(lst)

    def get_no_days_paid(self):
        worked_days = False
        number_of_days = False
        for line in self.worked_days_line_ids:
            number_of_days = line.number_of_days
            if not line.code == 'Unpaid' or not line.code == 'LATEMARK':
                worked_days = worked_days + number_of_days
        return worked_days    
    
    def get_total(self, slip_id, cat_code):
        cat_obj = self.env['hr.salary.rule.category'].search([('code', '=', cat_code)])
        lst = [line.total for line in slip_id.line_ids if line.category_id.id == cat_obj.id]
        return sum(lst)
    
#     @api.multi
#     @api.depends('line_ids')
    def get_section_total(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
#       Get the minimum value of declared sections
        section_list = []
        if fin_year:
            for year in self.employee_id.financial_year_ids:
                for declaration in year.it_declaration_ids:
                        section_list.append(declaration.section_id.name)
                        min_value = min(declaration.max_limit, declaration.declaration_total)
                        section_list.append(min_value)
        sec_list = [section_list[i:i + 2] for i  in range(0, len(section_list), 2)]
        self.row_list_right = sec_list
        return sec_list
    
    @api.multi
    @api.depends('line_ids')
    def get_total_declaration(self):
        for this in self:
            fin_year = this.env['financial.year.master'].search([('date_start', '<', this.date_from), ('date_end', '>', this.date_from)], limit=1)
            section_list = []
            total_amount = 0.0
            if fin_year:
                for year in this.employee_id.financial_year_ids:
                    for declaration in year.it_declaration_ids:
                            min_value = min(declaration.max_limit, declaration.declaration_total)
                            section_list.append(min_value)
                            total_amount = total_amount + min_value
            this.total_declarations = total_amount
    
    
    def get_left_rows(self):
        fin_year = self.env['financial.year.master'].search([('date_start', '<', self.date_from), ('date_end', '>', self.date_from)], limit=1)
#       Get the minimum value of declared sections
        section_list = []
        left_list = []
        if fin_year:
            for year in self.employee_id.financial_year_ids:
                for declaration in year.it_declaration_ids:
                        section_list.append(declaration.section_id.name)
                        min_value = min(declaration.max_limit, declaration.declaration_total)
                        section_list.append(min_value)
#         section_list = ['80C',150000,'80D',9000,'80D',780000,'80E',80000,'80F',9890,'80G',900000]
        sec_list = [section_list[i:i + 2] for i  in range(0, len(section_list), 2)]
        self.row_list_right = sec_list
        if len(sec_list) > 4:
            list_gap = len(sec_list) - 4
            for i in range(int(list_gap) * 4):
                left_list.append('')
            left_list = [left_list[i:i + 4] for i  in range(0, len(left_list), 4)]
        return left_list
        
        
    def get_right_rows(self):
        right_list = []
        if len(self.row_list_right) < 4:
            list_gap = 4 - len(self.row_list_right)
            for i in range(int(list_gap) * 2):
                right_list.append('')
            right_list = [right_list[i:i + 2] for i  in range(0, len(right_list), 2)]
        return right_list
    
    def get_lst_right_rows(self):
        last_right_list = []
        if len(self.last_row_list_left) > 0:
            list_gap = len(self.last_row_list_left) - 0
            for i in range(int(list_gap) * 2):
                last_right_list.append('')
            last_right_list = [last_right_list[i:i + 2] for i  in range(0, len(last_right_list), 2)]
        return last_right_list
            

class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    @api.onchange('name')
    def onchange_name(self):
        payslip_batch_id = self.search([('date_start', '>=', self.date_start), ('date_end', '<=', self.date_end)])
        if payslip_batch_id:
            raise Warning(_('Payslip batch has been already generated for the selected month'))
    
    @api.multi
    def print_payslip_batch_report(self):
        return self.env.ref('indian_payroll.payslip_batch_report')
#         value = self.env['report'].get_action(self, 'indian_payroll.payslip_batch_report')
#         return value
    @api.multi
    def get_deduction_rules(self, cat):
        categ_obj = self.env['hr.salary.rule.category'].search([('code', 'like', cat)], limit=1)
        cat_list = [line.code for slip in self.slip_ids for line in slip.line_ids if line.category_id.id == categ_obj.id]
        if cat == 'DED':
            self.ded_cat_list = list(set(cat_list))
        if cat == 'ALW':
            self.alw_cat_list = list(set(cat_list))
        return list(set(cat_list))
    @api.one
    def get_colspan(self, cat):
        categ_obj = self.env['hr.salary.rule.category'].search([('code', 'like', cat)], limit=1)
        cat_list = [line.code for slip in self.slip_ids for line in slip.line_ids if line.category_id.id == categ_obj.id]
        # print"cat_list---------",list(set(cat_list)),len(list(set(cat_list)))
        return len(list(set(cat_list)))
        
    @api.multi
    def get_amt_by_code(self, code, slip_id):
        line = self.env['hr.payslip.line'].search([('code', '=', code), ('slip_id', '=', slip_id.id)], limit=1)
        return line.total
    def get_current_date(self):
        if self.state == 'done':
            return self.write_date

class ITSlab(models.Model):
    _name = 'it.slab'
    _rec_name = 'person_type'
    person_type = fields.Selection([('male', 'Male'), ('female', 'Female'), ('senior_citizen', 'Senior Citizens')], 'Person', required=True)
    it_slab_line_ids = fields.One2many('it.slab.line', 'slab_id') 
    _sql_constraints = [
        ('person_type_unique', 'UNIQUE(person_type)',
         'Person must be unique!'),
    ]
class ITSlabLine(models.Model):
    _name = 'it.slab.line'
    
    slab_id = fields.Many2one('it.slab', 'Slab')
    from_amount = fields.Float('From')
    to_amount = fields.Float('To')
    tax_percent = fields.Float('Tax(%)')
    estimated_tax = fields.Float("Estimated Tax",compute='get_estimated_tax',store=True)
    
    @api.one
    @api.depends('from_amount', 'to_amount', 'tax_percent')
    def get_estimated_tax(self):
        #print "estimatedddddddd taxxxxxxxx   ",self
        for amount in self:
            amount_differance = amount.to_amount - amount.from_amount
            self.estimated_tax = (amount_differance*amount.tax_percent)/100
    
