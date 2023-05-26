from openerp import api, fields, models, _
from openerp.exceptions import UserError
import datetime

class Setting(models.Model):
    _name = 'setting.setting'
    _inherit = 'res.config.settings'

    point_achieved_amount = fields.Char("Points Achieved Amount")
    timesheet_time_per_day = fields.Float("Time Limit Per Day(In Hours)")
    timesheet_time_per_week = fields.Float("Time Limit Per Week(In Hours)")
    company_bussiness_date = fields.Date("Bussiness Date",default=datetime.datetime.strptime(str(datetime.datetime.now().year) + "-03-31 00:00:00", "%Y-%m-%d %H:%M:%S"))
    leaves_refreshed = fields.Boolean('Leaves Refreshed')
    
    @api.multi
    def set_point_achieved_amount(self):
        config_value = self.point_achieved_amount
        self.env['ir.values'].set_default('setting.setting', 'point_achieved_amount', config_value)

    @api.multi
    def set_timesheet_time_per_day(self):
        # if self.timesheet_time_per_day >= self.timesheet_time_per_week:
        #     raise UserError(_('Per Day Timit Limit Cannot Be Greater than Per Week Time Limit'))
        config_value = self.timesheet_time_per_day
        minutes = config_value - int(config_value)
        hours = int(config_value)
        minutes = round(minutes * 60)
        if hours > 24 or minutes > 60:
            raise UserError(_('Invalid time Format'))
        else:
            self.env['ir.values'].set_default('setting.setting', 'timesheet_time_per_day', config_value)

    @api.multi
    def set_timesheet_time_per_week(self):
        config_value = self.timesheet_time_per_week
        self.env['ir.values'].set_default('setting.setting', 'timesheet_time_per_week', config_value)
        
    @api.multi
    def set_company_bussiness_date(self):
        config_value = self.company_bussiness_date
        self.env['ir.values'].set_default('setting.setting', 'company_bussiness_date', config_value)
    
    @api.multi
    def set_leaves_refreshed(self):
        config_value = self.leaves_refreshed
        self.env['ir.values'].set_default('setting.setting', 'leaves_refreshed', config_value)
