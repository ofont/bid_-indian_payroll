# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _
from datetime import date,datetime
from openerp.exceptions import UserError,ValidationError,Warning
from operator import add

class FinancialYearMaster(models.Model):
    _name = 'financial.year.master'
    name = fields.Char('Name',required=True)
    date_start=fields.Date('Start Date')
    date_end=fields.Date('End Date')
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        item_ids=self.search([('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start)])
        if item_ids:
            raise Warning(_('Invalid Date range!'))
        return models.Model.create(self, vals)
    @api.multi
    def write(self, vals):
        res= models.Model.write(self, vals)
        item_ids=self.search([('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start)])
        if item_ids and item_ids!=self:
            raise Warning(_('Invalid Date range'))
        return res
    
class FinancialYear(models.Model):
    _name = 'declaration.financial.year'
    financial_year_id=fields.Many2one('financial.year.master','Financial Year',required=True)
    employee_id=fields.Many2one('hr.employee','Employee')
    it_declaration_ids=fields.One2many('it.declaration','declaration_financial_year',"Sections")#,_default='_get_section_lines')
    lock=fields.Boolean(' ')
    locking_date=fields.Date('Locking Date')
    
    _sql_constraints = [
        ('financial_year_id_unique', 'UNIQUE(financial_year_id,employee_id)',
         'Financial Year must be unique!'),
    ]
    
    @api.onchange('financial_year_id')
    def onchange_financial_year_id(self):
        config_obj=self.env['declaration.configuration'].search([('financial_year_id','=',self.financial_year_id.id)],limit=1)
        self.locking_date=config_obj.locking_date
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        same_line = self.search([('financial_year_id', '=', vals.get('financial_year_id', False)),('employee_id','=',vals.get('employee_id', False))])
        if same_line:
            raise Warning(_('Financial Year must be unique!!!'))
        else:
            return models.Model.create(self, vals)
    
    
    @api.multi
    def write(self, vals):
        res= super(FinancialYear, self).write(vals)
        same_line = self.search([('financial_year_id', '=', self.financial_year_id.id),('employee_id','=',self.employee_id.id)])
        if same_line and not same_line==self:
            raise Warning(_('Financial Year must be unique!!'))
        else:
            return res
    
class ITSection(models.Model):
    _name = 'it.section'
    name = fields.Char('Name',required=True)
    max_limit = fields.Float('Maximum Limit')
    declaration_ids=fields.One2many('declaration.declaration','section_id','Declarations')
    
class Declaration(models.Model):
    _name = 'declaration.declaration'
    name = fields.Char('Name',required=True)
    section_id = fields.Many2one('it.section', "IT Section",required=True)
    
    
class ITDeclaration(models.Model):
    _name = 'it.declaration'
    section_id = fields.Many2one('it.section', "IT Section",required=True)
    declaration_line_ids=fields.One2many('it.declaration.line', 'declaration_id','Declarations')
    employee_id=fields.Many2one('hr.employee', "Employee")
    max_limit = fields.Float('Maximum Limit',related='section_id.max_limit',store=True)
    declaration_total = fields.Float('Total Declaration',compute="get_declaration_total",store=True)
    declaration_financial_year=fields.Many2one('declaration.financial.year')
#     declaration_id=fields.Many2one('declaration.declaration',required=True)
    @api.multi
    @api.depends('declaration_line_ids','declaration_line_ids.amount')
    def get_declaration_total(self):
        for this in self :
            sum=0
            for line in this.declaration_line_ids:
                sum+=line.amount
            this.declaration_total=sum
    
    _sql_constraints = [
    ('section_id_declaration_financial_year_uniq', 'unique(section_id,declaration_financial_year)', 'Section must be unique!!!!!!!!')
    ]
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        
        same_line = self.search([('section_id', '=', vals.get('section_id', False)),
                                 ('declaration_financial_year', '=', vals.get('declaration_financial_year', False))])
        if same_line:
            raise Warning(_('Section must be unique!'))
        if vals.get('max_limit', False) <  vals.get('declaration_total', False):
            raise Warning(_('Total Declaration must be less than max limit.'))
        else:
            return models.Model.create(self, vals)
    
    @api.multi
    def write(self, vals):
        res=models.Model.write(self, vals)
        same_line = self.search([('section_id', '=', self.section_id.id),
                                 ('declaration_financial_year', '=', self.declaration_financial_year.id)])
        if same_line and not same_line==self:
            raise Warning(_('Section must be unique!!'))
        
        if self.max_limit<self.declaration_total:
            raise Warning(_('Total Declaration must be less than max limit.'))
        else:
            return res
            
class ITDeclarationLine(models.Model):
    _name = 'it.declaration.line'
    declaration_id = fields.Many2one('it.declaration', "Declaration",required=False)
    it_declaration_id=fields.Many2one('declaration.declaration', "IT Declaration")
    amount=fields.Float('Amount')
    status=fields.Boolean('Verified')
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], default='draft')
    attachment_line_ids = fields.One2many('ir.attachment', 'declaration_line_id', 'Attachments')
    
    @api.onchange('it_declaration_id')
    def onchange_it_declaration_id(self):
        return {'domain': {'it_declaration_id': [('section_id', '=', self._context.get('section_id'))]}}
    
class IrAttachment(models.Model):
    _inherit = "ir.attachment"
    
    declaration_line_id = fields.Many2one('it.declaration.line', 'Declaration')
    
    
    
class DeclarationConfiguration(models.Model):
    _name = 'declaration.configuration'
    _rec_name='locking_date'
    locking_date=fields.Date('Locking Date')
    financial_year_id=fields.Many2one('financial.year.master','Financial Year')
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)], auto_join=True,
                                readonly=True)
    @api.model
    def create(self, vals):
        """"Creating Audit Trail"""
        same_line = self.search([('financial_year_id', '=', vals.get('financial_year_id', False))])
#         print "same_line------------",same_line,vals.get('financial_year_id', False)
        if same_line:
            raise Warning(_('Financial Year must be unique'))
        lst=[]
        msg_ids = {
            'date': datetime.now(),
            'model': 'declaration.configuration',
            'financial_year_id':vals.get('financial_year_id'),
            'locking_date':vals.get('locking_date'),
            'author_id':(self.env['res.users'].browse(self._context.get('uid'))).partner_id.id,
        }
        lst.append((0, 0, msg_ids))
        vals.update({'mesge_ids': lst})
        res= super(DeclarationConfiguration, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        """"Creating Audit Trail"""
        same_line = self.search([('financial_year_id', '=', vals.get('financial_year_id', False))])
        #print "same_line------------",self,same_line,vals.get('financial_year_id', False)
        if same_line and not same_line==self:
            raise Warning(_('Financial Year must be unique'))
        
        lst=[]
        msg_ids = {
            'date': datetime.now(),
            'model': 'declaration.configuration',
            'financial_year_id':vals.get('financial_year_id')if vals.get('financial_year_id') else self.financial_year_id.id,
            'locking_date':vals.get('locking_date') if vals.get('locking_date') else self.locking_date,
            'author_id':(self.env['res.users'].browse(self._context.get('uid'))).partner_id.id,
        }
        self.env['mail.messages'].write(msg_ids)
        lst.append((0, 0, msg_ids))
        vals.update({'mesge_ids': lst})
        res= models.Model.write(self, vals)
        declaration_obj=self.env['declaration.financial.year'].search([('financial_year_id','=',self.financial_year_id.id)])
        for declaration in declaration_obj:
            if self.locking_date<=str(datetime.now().date()):
#                 print "if-------------",self.locking_date,str(datetime.now().date())
                declaration.lock=True
            else:
#                 print "else-------------",self.locking_date,str(datetime.now().date())
                declaration.lock=False
        return res
    
    @api.model
    @api.depends('self')
    def lock_employee_declaration(self):
        for config in self.search([]):
            declaration_obj=self.env['declaration.financial.year'].search([('financial_year_id','=',config.financial_year_id.id)])
            for declaration in declaration_obj:
                if config.locking_date<=str(datetime.now().date()):
                    declaration.lock=True
                else:
                    declaration.lock=False
