from openerp import api, fields, models, _

class ResUsers(models.Model):
    _inherit = "res.users"
    
    emp_id = fields.Many2one('hr.employee', 'Employee ID')