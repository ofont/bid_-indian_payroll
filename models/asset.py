from openerp import fields, models, api, _
import datetime
from openerp.exceptions import UserError

class asset_product(models.Model):
    _name = "asset.product"
    
    name = fields.Char("Name")
    asset_seq_id = fields.Char("Asset Class")
    
    @api.model
    def create(self,vals):
        vals['asset_seq_id'] = self.env['ir.sequence'].get('asset.product')
        return super(asset_product, self).create(vals)

class asset_employee(models.Model):
    _name = "asset.product.line"
    
    name = fields.Char('Description',required=True)
    product_id = fields.Many2one('asset.product','Asset Product',required=True)
    hr_id = fields.Many2one('hr.employee','Employee')
    issue_date = fields.Date('Issue Date')
    is_surrendered = fields.Boolean('Surrendered',default=False)
    surrender_date = fields.Date('Surrender Date')
    is_damage = fields.Boolean('Damaged',default=False)
    dmg_desc = fields.Char('Damage Description')
    product_serial_number = fields.Char('Asset ID',required=True)

    @api.onchange('is_surrendered')
    def _onchange_surrendered(self):
        if not self.is_surrendered:
            self.surrender_date = None
        else:
            self.surrender_date = datetime.datetime.now()
    
    @api.onchange('is_damage')
    def _onchange_damage(self):
        if not self.is_damage:
            self.dmg_desc = None
    
    @api.onchange('product_serial_number')
    def _onchange_asset_Id(self):
        present = self.search([('product_serial_number','=',self.product_serial_number),('is_surrendered','=',False)])
        if present:
            raise UserError(_('Asset Id %s is not Available.') % (self.product_serial_number))
        return
        
    @api.model
    def create(self, vals):
        present = False
        if vals.get('product_serial_number'):
            present = self.search([('product_serial_number','=',vals.get('product_serial_number')),('is_surrendered','=',False)])
        if present:
            raise UserError(_('Asset Id %s is not Available.') % (vals.get('product_serial_number')))
        else:
            return super(asset_employee,self).create(vals)