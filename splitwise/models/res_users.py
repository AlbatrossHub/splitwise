from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    list_in_splitwise = fields.Boolean(string='List in Splitwise', default=False)
