from openerp import api, fields, models, _
from openerp.exceptions import UserError
from datetime import datetime, timedelta, date

class HrTimeSheetSheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'
    
    employee_id = fields.Many2one('hr.employee', 'Employee')
    
class HrProjects(models.Model):
    _name = "hr.projects"

    name = fields.Char('Project Name')
    task_ids = fields.One2many('account.analytic.account', 'project_id', 'Tasks')


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    project_id = fields.Many2one('hr.projects', 'Project',required=True)
    comments = fields.Text('Additional Comments')


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model
    def check_if_has_leave(self, input_date, emp):
        leaves = self.env['hr.leave'].search([('employee_id', '=', emp.id), ('state', '=', 'confirm')])
        for eachLeave in leaves:
            dateFrom = (datetime.strptime((eachLeave.date_from).split(' ')[0], "%Y-%m-%d")).date()
            dateTo = (datetime.strptime((eachLeave.date_to).split(' ')[0], "%Y-%m-%d")).date()
            if (input_date >= dateFrom and input_date <= dateTo):
                raise UserError("You have leave confirmed on %s!\nCannot make entry for it." % (input_date,))

    @api.model
    def check_if_public_holiday(self, input_date):
        publicHolidays = self.env['hr.public.holidays'].search([])
        for eachPublicHoliday in publicHolidays:
            holidayDate = (datetime.strptime(eachPublicHoliday.date, "%Y-%m-%d")).date()
            if input_date == holidayDate:
                raise UserError("Date %s is a public Holiday!\nCannot make entry for it." % (input_date,))

    @api.model
    def check_time_limit(self, input_time, input_date, sheet_id):
        day_limit = self.env['ir.values'].get_default('setting.setting', 'timesheet_time_per_day');
        input_time = float(input_time)
        sumOfHours = 0
        for eachTmId in sheet_id.timesheet_ids:
            eachTmDate = (datetime.strptime((eachTmId.date).split(' ')[0], "%Y-%m-%d")).date()
            if input_date == eachTmDate and self.id != eachTmId.id:
                sumOfHours += eachTmId.unit_amount
        if day_limit:
            sumOfHours += input_time
            if sumOfHours > day_limit:
                raise UserError("Time Exceeds Per Day Limit")
    
    @api.model
    def check_timesheet_till_today(self, input_time, input_date, sheet_id):
#         if(input_time):
        today = datetime.now().date()
        if input_date > today:
            raise UserError("Cannot enter for %s which is after today" % (input_date,))
            

    @api.model
    def create(self, vals):
        day_limit = self.env['ir.values'].get_default('setting.setting', 'timesheet_time_per_day');
        input_time = float(vals['unit_amount'])
        sheetObj = self.env['hr_timesheet_sheet.sheet'].browse(vals.get('sheet_id'))
        input_date = (datetime.strptime(str(vals.get('date')).split(' ')[0], "%Y-%m-%d")).date()
        self.check_if_has_leave(input_date, sheetObj.employee_id)
        self.check_if_public_holiday(input_date)
        error = False
        if (day_limit):
            if input_time > day_limit:
                error = True
                raise UserError("Time Exceeds Per Day Limit")
            else:
                self.check_time_limit(input_time, input_date, self.sheet_id)
                self.check_timesheet_till_today(input_time, input_date, self.sheet_id)
        if not error:
            return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        result = super(AccountAnalyticLine, self).write(vals)
        day_limit = self.env['ir.values'].get_default('setting.setting', 'timesheet_time_per_day');
        input_time = self.unit_amount
        input_date = (datetime.strptime((self.date).split(' ')[0], "%Y-%m-%d")).date()
        self.check_if_has_leave(input_date, self.sheet_id.employee_id)
        self.check_if_public_holiday(input_date)
        if (day_limit):
            if input_time > day_limit:
                raise UserError("Time Exceeds Per Day Limit")
            else:
                self.check_time_limit(input_time, input_date, self.sheet_id)
                self.check_timesheet_till_today(input_time, input_date, self.sheet_id)
        return result
    
    
