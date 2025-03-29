from odoo import models, fields, api

class IronLog(models.Model):
    _name = 'iron.log'
    _description = 'Dhobi Log'
    _order = 'create_date desc'

    no_of_clothes = fields.Integer(string='Qty', required=True)
    create_date = fields.Datetime("Create Date", readonly=True)