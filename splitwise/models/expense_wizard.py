from odoo import models, fields, api

class AddExpenseWizard(models.TransientModel):
    _name = 'expense.add.wizard'
    _description = 'Add Expense Wizard'

    name = fields.Char(string='Expense Name', required=True)
    amount = fields.Float(string='Amount', required=True)
    participant_ids = fields.Many2many('res.users', string='Participants', required=True, domain=[('list_in_splitwise', '=', True)])
    group_id = fields.Many2one('expense.group', string='Group', required=True)
    expense_paid_by = fields.Many2one('res.users', string='Paid By', default=lambda self: self.env.user, required=True, domain=[('list_in_splitwise', '=', True)])

    @api.model
    def default_get(self, fields):
        res = super(AddExpenseWizard, self).default_get(fields)
        res['group_id'] = self.env.context.get('active_id')
        res['participant_ids'] = [(6, 0, self.env.context.get('default_participants', []))]
        return res

    def action_create_expense(self):
        self.ensure_one()
        self.env['expense.expense'].create({
            'name': self.name,
            'amount': self.amount,
            'expense_paid_by': self.expense_paid_by.id,
            'group_id': self.group_id.id,
            'participant_ids': [(6, 0, self.participant_ids.ids)],
        })
        return {'type': 'ir.actions.act_window_close'}
