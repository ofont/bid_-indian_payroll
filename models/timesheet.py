from openerp import api, fields, models, _
import datetime as DateTime
import calendar

class HrPublicHolidays(models.Model):
    _name = "hr.public.holidays"

    name = fields.Char('Holiday Name', help='Name of occasion for which holiday is defined', required=True)
    date = fields.Date('Date', help='Date of occasion', required=True)
    comment = fields.Text('Comments', help='Description or extra comments for holiday')
    day = fields.Char('Day')

    @api.onchange('date')
    def onchange_date(self):
        if self and self.date:
            date_obj = DateTime.datetime(int(str(self.date).split('-')[0]), int(str(self.date).split('-')[1]), int(str(self.date).split('-')[2]))
            self.day = calendar.day_name[date_obj.weekday()]