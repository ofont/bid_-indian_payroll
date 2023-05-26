import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _

document_type = [('ssc', 'Secondary School Certificate'), ('hsc', 'Higher School Certificate'), ('degree_mark', 'Degree Marksheet'),
                 ('degree_certi', 'Degree Certificate'), ('pg_mark', 'Post Graduate Marksheet'), ('pg_certi', 'Post Graduate Certificate'),
                 ('add_proof', 'Address Proof'), ('id_proof', 'ID Proof'), ('exp_certi', 'Experience Certificate'),
                 ('reliv_certi', 'Reliving Certificate'),
                 ('termination', 'Termination Certificate'),
                 ('emp_form', 'Offer Letter 1st Page'), ('emp_form2', 'Offer Letter Last Page'), ('resume', 'Resume Page 1'),
                 ('resume2', 'Resume Page 2'), ('resume3', 'Resume Page 3'), ('other', 'Other')]

class ir_attachment(models.Model):
    _inherit = "ir.attachment"
    
    job_position = fields.Many2one('hr.job','Applying for position',help="Select for which job position to be applied")
    is_open = fields.Boolean('Open Resume',default = True)
    
    @api.model
    def _get_doc_types(self):
        """
        To get attachment type
        """
        type_list = ['ssc', 'hsc', 'degree_mark', 'degree_certi', 'pg_mark', 'pg_certi', 'add_proof', 'id_proof',
                     'exp_certi', 'reliv_certi', 'termination', 'emp_form', 'emp_form2', 'resume', 'resume2', 'resume3', 'other']
        return [(r[0], r[1]) for r in document_type if r[0] in type_list]

    types = fields.Selection('_get_doc_types', 'Attachment Types', required=True, default='other')
    datas = fields.Binary('Data', required=True)
    emp_attach_id = fields.Many2one('hr.employee', 'Employee')
    doc_attach_id = fields.Many2one('hr.public.documents', 'Policy Documents')
    
