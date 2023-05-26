from openerp import api, fields, models


class MailMessage(models.Model):
    _name = 'mail.messages'
    _description = 'Mail Messages'

    @api.model
    def _get_default_author(self):
        return self.env.user.partner_id
    
    
    res_id = fields.Integer('Related Document ID', select=1)
    date = fields.Datetime('Date', default=fields.Datetime.now)
    author_id = fields.Many2one(
        'res.partner', 'UserName', select=1,
        ondelete='set null', default=_get_default_author,
        help="Author of the message. If not set, email_from may hold an email address that did not match any partner.")
    model = fields.Char('Related Document Model', select=1)
    locking_date=fields.Date('Locking Date')
    financial_year_id=fields.Many2one('financial.year.master','Financial Year')
