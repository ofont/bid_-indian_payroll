from openerp import api, fields, models, _
from openerp.exceptions import Warning
from openerp.http import request
import openerp.addons.decimal_precision as dp
from dateutil import relativedelta
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from openerp.exceptions import UserError, ValidationError
from openerp.tools.safe_eval import safe_eval as eval
# from oprnerp.tools.safe_eval import safe_eval


class hr_contract(models.Model):
    _inherit = 'hr.contract'
    line_ids = fields.One2many('hr.contract.line', 'slip_id', string='contract Lines', readonly=True)
    employee_ctc = fields.Char("Monthly Gross Amount" ,readonly=True)
    contract_code = fields.Char("Code")
    contract_amount = fields.Float('Amount')
    contract_name = fields.Char("Name")
    total_income = fields.Float('Total Income', compute="get_total_income", store=True)
    taxable_income = fields.Float('Taxable Income', compute="get_taxable_income", store=True)
    yearly_tds = fields.Float('Yearly TDS', compute="get_yearly_tds", store=True)
    
    
    @api.multi
    @api.depends('line_ids')
    def get_total_income(self):
        for rec in self:
#             print ("ctccccccccccccccccc   ",rec.employee_ctc)
            if float(rec.employee_ctc )> 0.0:
                rec.total_income = (float(rec.employee_ctc) * 12)
                
    #@api.multi
    @api.depends('line_ids', 'total_income')
    def get_taxable_income(self):
#         print ( "Sellllllllllllllllllllll   ",self)
        for hr in self:
            declarations = [dec.amount for year in hr.employee_id.financial_year_ids for section in year.it_declaration_ids for dec in section.declaration_line_ids]
#             print ("declaratinssssssssssssss ",declarations)
            hr.taxable_income = round(hr.total_income - sum(declarations))

    @api.multi
    @api.depends('line_ids', 'total_income', 'taxable_income')
    def get_yearly_tds(self):
#         print("\n self----------------->>>>>",self)
        for cont in self:
#             print("\n contract id---------self----line-------::::",cont.line_ids.amount)
            declarations = [cont.employee_ctc for year in cont.employee_id.financial_year_ids for section in year.it_declaration_ids for dec in section.declaration_line_ids]
#             print("\n declastion as-------------->>>>",declarations,cont.total_income)
            if declarations!=[]:
                decl=(int(declarations[0]))
            else:
                decl=0
            taxable_income = round(cont.total_income - (decl))
            slab = cont.env['it.slab'].search([('person_type', '=', cont.employee_id.gender)], limit=1)
            slab_line = cont.env['it.slab.line'].search([('from_amount', '<', taxable_income), ('to_amount', '>=', taxable_income), ('slab_id', '=', slab.id)], limit=1)
#             print("\n slab_line----------->>>",slab,slab_line)
            tds1=0
            for line in slab.it_slab_line_ids:
#                 print("\n \n in td s----------11---->>>ifffff",taxable_income,line.to_amount)
                if taxable_income>=line.to_amount:
#                     print("\n \n in td s---------1222----->>>ifffff",taxable_income,line.to_amount)
                    tds1=tds1+line.estimated_tax
            tds2=(slab_line.tax_percent/100)*(taxable_income-slab_line.from_amount)
            cont.yearly_tds = tds2+tds1
            projected_tds = cont.yearly_tds / 12
#             print ("Project tesssssssssssssssss ",projected_tds, cont.tds,"==")
            if projected_tds:
                cont.tds = projected_tds
#                 print( "cont.tds  ",cont.tds)
                cont._cr.execute('update hr_contract set tds=%s where id=%s', (projected_tds, cont.id))

    @api.depends('employee_id')
    @api.onchange('job_id')
    def onchange_job_id(self):
        today = datetime.today()
        if not self.employee_id:
            return
        todayDate = datetime.today()
        if todayDate.day > 25:
            todayDate += timedelta(7)
        start_date = todayDate.replace(day=1)
        end_date = todayDate.replace(day=28)
#         worked_days_line_ids = self.get_worked_day_lines(start_date, end_date)
    
    def get_current_date(self):
#         print ("\n\n\nget current Date ============ ",date.today())
        now = datetime.now()
#         print ("noewwwwwwwwww ",now)
        date_string = now.strftime('%Y-%m-%d')
        current_date = "Date : " + date_string
        return current_date
    
    def get_earning_heads(self, earnings):
        amount = 0
        for payslip in self:
            payslip.line_ids.unlink()
            contract_ids = [payslip.id]
        
        lines = [line for line in self.get_payslip_lines(contract_ids, payslip.id)]
        for line in lines:
            if type(line['amount']) == float and line['code'] != 'NET':
#                 print ("\n\n\nLinesssssssssssssss  ",line)
#                 print ("Name  ",line['name'])
#                 print ("Code  ",line['code'])
#                 print ("Amounttttttt ",line['amount'], type(line['amount']))
                if earnings == line['code']:
#                     print ("amounrrrrrr ",line['amount'])
                    amount =  line['amount']
                
            else:
                print ("]]]]]]]]]]]]]]====================================")
            
        return amount
    
    
#     @api.depends('struct_id')
#     @api.onchange('wage')
#     def onchange_wage(self):
#         print "\n\n\n\nSelffffffffffffffffffff   ",self.wage
#         sal_rule_categ_obj = self.env['hr.salary.rule.category']
#         if self.struct_id:
#             print "Present salary structure is ",self.struct_id
#             data_query =  '''select struct.name, struct.parent_id ,rule.code, rule.condition_range, rule.amount_fix, rule.amount_percentage, rule.condition_select, rule.amount_percentage_base, 
#             rule.amount_select, rule.condition_python, rule.amount_python_compute, rule.category_id,quantity 
#             from hr_payroll_structure as struct, hr_salary_rule as rule,hr_structure_salary_rule_rel as hssr 
#             where struct.id = hssr.struct_id and rule.id = hssr.rule_id and struct.id= %s'''%(self.struct_id.id)
#             request.cr.execute(data_query)
#             basic = self.wage
#             struct_ids = request.cr.dictfetchall()
# #             print "\nstrucccccccccccttttttttttttttt idsssssss  ",struct_ids
#             for payroll in struct_ids:
# #                 print "\nPayroll ",payroll
# #                 print "\nFixed valueeeee ========= ",payroll['condition_select']
#                 
#                 category_ids = sal_rule_categ_obj.search([('id', '=',payroll['category_id'])])
#                 if category_ids.code == 'ALW':
#                     if payroll['amount_select'] == 'fix':
#                         print "Fixed ",payroll['amount_fix']
#                     elif payroll['amount_select'] == 'code':
#                         print "Codeeeee",payroll['amount_python_compute']
#                     elif payroll['amount_select'] == 'percentage':
#                         print "\n\nPercentage",payroll['amount_percentage_base']
#                         print "Percentage",payroll['amount_percentage']

    @api.multi
    def unlink(self):
        return super(hr_contract, self).unlink()
    
        
    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        #a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        #OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids
                        
                        
#             
    @api.multi
    def compute_sheet(self):
        for payslip in self:
            #delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = [payslip.id]
            lines = [(0, 0, line) for line in self.get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines})
        return True
    
    @api.model
    def get_worked_day_lines(self, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, datetime_day):
            day = fields.Date.to_string(datetime_day)
            return self.env['hr.leave'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', day),
                ('date_to', '>=', day)
            ], limit=1).holiday_status_id.name

        res = []
        #fill only if the contract as a working schedule linked
        for contract in self:
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                working_hours_on_day = contract.working_hours.working_hours_on_day(day_from + timedelta(days=day))
                if working_hours_on_day:
                    #the employee had to work
                    leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day))
                    if leave_type:
                        #if he was on leave, fill the leaves dict
                        if leave_type in leaves:
                            leaves[leave_type]['number_of_days'] += 1.0
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day
                        else:
                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 5,
                                'code': leave_type,
                                'number_of_days': 1.0,
                                'number_of_hours': working_hours_on_day,
                                'contract_id': contract.id,
                            }
                    else:
                        #add the input vals to tmp (increment if existing)
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += working_hours_on_day
            leaves = [value for key, value in leaves.items()]
            res += [attendances] + leaves
        return res

            
    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict
            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0
                
#         class InputLine(BrowsableObject):
            
        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0
        class Payslips(BrowsableObject):
             """a class that will be used into the python code, mainly for usability purposes"""

            
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.contract'].browse(payslip_id)
        categories = BrowsableObject(payslip.employee_id.id, {})
        payslips = Payslips(payslip.employee_id.id, payslip)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict)
        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': 30}
        contracts = self.browse(contract_ids)
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
#                 print "@@@@@@@#########%$$$$$$$$$$$$%%%%%%%%%%%%%%% ",localdict['GROSS']
                #check if the rule can be applied
                
                
                if rule.satisfy_condition(localdict) and rule.id not in blacklist and not rule.code == "LOP":
                    if not rule.input_ids.id:
#                         print ("---------------------------------")
                        #compute the amount of the rule
                        amount, qty, rate = rule.compute_rule(localdict)
                        #check if there is already a rule computed with that code
                        previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                        #set/overwrite the amount computed for this rule in the localdict
                        tot_rule = amount * qty * rate / 100.0
                        localdict[rule.code] = tot_rule
                        rules_dict[rule.code] = rule
                        #sum the amount for its salary category
                        localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
#                         print ("***********************************************")
                        #create/overwrite the rule in the temporary results
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                    else:
                        print ("==========================")
#                         blacklist += [id for id, seq in rule._recursive_search_of_rules()]
                else:
                    print ("-^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                    #blacklist this rule and its children
#                     blacklist += [id for id, seq in rule._recursive_search_of_rules()]
#                     blacklist += [id for id, seq in self.env['hr.salary.rule']._recursive_search_of_rules()]
        if 'GROSS' in localdict:
            print("\n\n -------------Grosss-+++++++",self.employee_ctc ,int(localdict['GROSS']))
            self.employee_ctc = int(localdict['GROSS']) 
        else:
            print ("-")
        return [value for code, value in result_dict.items()]
#         return True

class hr_contract_line(models.Model):
    '''
    contract Line
    '''

    _name = 'hr.contract.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'sequence'
    slip_id =fields.Many2one('hr.contract', 'Pay Slip', required=True, ondelete='cascade')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Rule')
    employee_id = fields.Many2one('hr.employee', 'Employee', )
    name = fields.Char('Name')
    rate  = fields.Float('Rate (%)', digits_compute=dp.get_precision('Payroll Rate'))
    amount =  fields.Float('Amount', digits_compute=dp.get_precision('Payroll'))
    quantity = fields.Float('Quantity', digits_compute=dp.get_precision('Payroll'))
    total = fields.Float(compute='_compute_total', string='Total', digits=dp.get_precision('Payroll'), store=True)
    
    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100
    
class hr_salary_rule(models.Model):

    _inherit = 'hr.salary.rule'
    
#     @api.multi
#     def _recursive_search_of_rules(self):
#         """
#         @param rule_ids: list of browse record
#         @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
#         """
#         print "\n\n\nRUleeeeee IDSSSSSSSSSSSSSSSS   ",self
#         children_rules = []
#         for rule in self:
#             print "Ruleeeeeeeeeee ^^^^^^^^^^^^^^^^^ ",rule, rule.id
#             print "Chilllllldddddddddddd Idddddddddd ",rule.id.id
#             for child in rule.id:
#                 print "======================   ",child
#                 print "************  "
#                 children_rules += self._recursive_search_of_rules(rule.child_ids)
#         print"==============================  return  ",[(r.id, r.sequence) for r in self] + children_rules
#         return [(r.id, r.sequence) for r in self] + children_rules
#     
#     def _recursive_search_of_rules(self):
#         """
#         @param rule_ids: list of browse record
#         @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
#         """
#         children_rules = []
#         for rule in self:
#             print "Ruleeeeeeeeeeeeee ",rule
#             for child in rule.id:
#                 print "Chileeeeeeddddddddddddddddd ",child
#                 if child.child_ids:
#                     children_rules += self._recursive_search_of_rules(child.child_ids)
#         return [(r.id, r.sequence) for r in self] + children_rules
     
    
#     @api.multi
#     def _recursive_search_of_rules(self):
#         """
#         @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
#         """
#         children_rules = []
#         for rule in self.filtered(lambda rule: rule.child_ids):
#             print "Ruleeeeeeeeeee ^^^^^^^^^^^^^^^^^ ",rule, type(rule)
#             children_rules += rule.child_ids._recursive_search_of_rules()
#         return [(rule.id, rule.sequence) for rule in self] + children_rules
#     
    @api.multi
    def satisfy_condition(self, localdict):
        """
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the given contract. Return False otherwise.
        """
        self.ensure_one()
 
         
        if self.condition_select == 'none':
            return True
        elif self.condition_select == 'range':
            try:
                result = eval(self.condition_range, localdict)
                return self.condition_range_min <= result and result <= self.condition_range_max or False
            except:
                raise UserError(_('Wrong range condition defined for salary rule %s (%s).') % (self.name, self.code))
        else:  # python code
            try:
                eval(self.condition_python, localdict, mode='exec', nocopy=True)
                     
                return 'result' in localdict and localdict['result'] or False
            except:
                raise UserError(_('Wrong python condition defined for salary rule %s (%s).') % (self.name, self.code))
#             
    @api.multi
    def compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(eval(self.amount_percentage_base, localdict)),
                        float(eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).') % (self.name, self.code))
        else:
            try:
                eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            except:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))

#     total = fields.function(_calculate_total, method=True, type='float', string='Total', digits_compute=dp.get_precision('Payroll'),store=True )
    