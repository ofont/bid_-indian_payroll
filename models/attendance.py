from odoo import api, fields, models, _
import pytz

import os
import logging
_logger = logging.getLogger(__name__)

# from datetime import datetime
import glob
from xlrd import open_workbook
# from datetime import date, timedelta
from datetime import datetime, date

class HrAttendance(models.Model):
    """
    Form for Attachment details
    """
    _inherit = "hr.attendance"

    @api.multi
    def import_attendance(self):
        fold_path = self.env['hr.attendance.config.setting'].search([], limit=1)
        folder = fold_path.folder_path
        if folder:
            timezone = fold_path.tz
            os.chdir(folder)
            today = date.today()
            file_date = str(today) + '.xlsx'
            lists = glob.glob(file_date)
            if lists:
                wb = open_workbook(lists[0])
                for s in wb.sheets():
                    #             for row in range(s.nrows):
                    for row in range(1, s.nrows):
                        for col in range(s.ncols):
                            value = (s.cell(row, col).value)
                            emp_name = s.cell(row, 4).value
                            sign_in = s.cell(row, 8).value
                            sign_out = s.cell(row, 9).value
                            code = s.cell(row, 2).value

                            if str(sign_in) == "00:00":
                                name = str(today) + ' ' + sign_in + ':00'
                            else:
                                name = str(today) + ' ' + sign_in[:8]
                            if str(sign_out) == "00:00":
                                name1 = str(today) + ' ' + sign_out + ':00'
                            else:
                                name1 = str(today) + ' ' + sign_out[:8]

                            local = pytz.timezone(timezone)

                            names = datetime.strptime(name, '%Y-%m-%d %H:%M:%S')
                            names1 = datetime.strptime(name1, '%Y-%m-%d %H:%M:%S')

                            local_dt_name = local.localize(names, is_dst=None)
                            utc_dt_name = local_dt_name.astimezone(pytz.utc)
                            name_st = str(utc_dt_name)
                            atte_name = name_st.split('+')[0]

                            local_dt_name1 = local.localize(names1, is_dst=None)

                            utc_dt_name1 = local_dt_name1.astimezone(pytz.utc)

                            name_st1 = str(utc_dt_name1)
                            atte_names = name_st1.split('+')[0]

                        if str(sign_in) == "00:00" and str(sign_out) == "00:00":
                            pass
                        else:
                            emp = self.env["hr.employee"].search([('code', '=', int(code))])
                            if emp:
                                self.env['hr.attendance'].create({
                                    'employee_id': emp.id,
                                    'action': 'sign_in',
                                    'name': atte_name,
                                })

                                self.env['hr.attendance'].create({
                                    'employee_id': emp.id,
                                    'action': 'sign_out',
                                    'name': atte_names,
                                })

        return True


class HrAttendanceConfigSetting(models.Model):
    _name = "hr.attendance.config.setting"

    folder_path = fields.Char("Folder Path",required=True)
    tz = fields.Selection('_tz_get', 'Timezone', default='Asia/Kolkata')

    @api.model
    def _tz_get(self):
        # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]
