from openerp import fields, models

class HrPolicyDocuments(models.Model):
    
    _name = 'hr.public.documents'
    
    name = fields.Char('Name',required = True)
    policy_doc = fields.Binary('Policy Document')
    document_attach_ids = fields.One2many('ir.attachment', 'doc_attach_id', 'No. of documents')