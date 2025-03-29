from io import StringIO
import base64
import csv
from odoo import models, fields, api

class ExpenseGroup(models.Model):
    _name = 'expense.group'
    _description = 'Expense Group'
    _order = 'create_date desc'

    name = fields.Char(string='Group Name', required=True)
    member_ids = fields.Many2many( 'res.users', string='Members', domain=[('list_in_splitwise', '=', True)])
    expense_ids = fields.One2many('expense.expense', 'group_id', string='Expenses')
    create_date = fields.Datetime("Create Date", readonly=True)
    split_ids = fields.One2many('expense.split', string='Splits', compute='_compute_split_ids')

    def action_add_expense(self):
        self.ensure_one()
        return {
            'name': 'Add Expense',
            'type': 'ir.actions.act_window',
            'res_model': 'expense.add.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_participants': self.member_ids.ids,
                'default_group_id': self.id,
            },
        }

    @api.depends('expense_ids.participant_ids')
    def _compute_split_ids(self):
        for group in self:
            splits = self.env['expense.split'].search([('expense_id.group_id', '=', group.id)])
            group.split_ids = splits

    def action_export_expenses(self):
        self.ensure_one()
        # Create CSV data
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        header = ['Date', 'Description', 'Cost'] + [user.name for user in self.member_ids]
        writer.writerow(header)

        # Write expense rows
        for expense in self.expense_ids:
            row = [expense.create_date.strftime('%Y-%m-%d'), expense.name, expense.amount]
            splits = {split.user_id.id: split.amount for split in expense.split_ids}
            row.extend(splits.get(user.id, 0) for user in self.member_ids)
            writer.writerow(row)

        # Write total row
        total_row = ['Total balance', 'ALL EXPENSES']
        total_amount = sum(expense.amount for expense in self.expense_ids)
        total_row.append(total_amount)
        total_row.extend(sum(split.amount for expense in self.expense_ids for split in expense.split_ids if split.user_id == user) for user in self.member_ids)
        writer.writerow(total_row)

        # Prepare file data
        file_data = base64.b64encode(output.getvalue().encode('utf-8')).decode('utf-8')
        output.close()

        # Create attachment
        attachment_obj = self.env['ir.attachment']
        attachment = attachment_obj.create({
            'name': 'Expenses.csv',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'Expenses.csv',
            'mimetype': 'text/csv',
        })

        # Return action to download the file
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'res_id': attachment.id,
            'target': 'new',
        }

class Expense(models.Model):
    _name = 'expense.expense'
    _description = 'Expense'

    name = fields.Char(string='Expense Name', required=True)
    amount = fields.Float(string='Amount', required=True)
    group_id = fields.Many2one('expense.group', string='Group', required=True, ondelete='cascade')
    participant_ids = fields.Many2many('res.users', string='Participants', domain=[('list_in_splitwise', '=', True)])
    split_ids = fields.One2many('expense.split', 'expense_id', string='Splits', readonly=True)  # Added this field
    expense_paid_by = fields.Many2one('res.users', string='Paid By', default=lambda self: self.env.user, required=True)

    @api.model
    def create(self, vals):
        record = super(Expense, self).create(vals)
        record._update_split_records()
        return record

    def write(self, vals):
        res = super(Expense, self).write(vals)
        self._update_split_records()
        return res

    def _update_split_records(self):
        """Update the associated expense.split records."""
        for expense in self:
            total_participants = len(expense.participant_ids)
            share_amount = expense.amount / total_participants if total_participants else 0
            
            # Delete old splits
            expense.split_ids.unlink()
            
            # Create updated splits
            for participant in expense.participant_ids:
                split_amount = share_amount
                if participant == expense.expense_paid_by:
                    split_amount = expense.amount - share_amount
                else:
                    split_amount = -share_amount

                self.env['expense.split'].create({
                    'user_id': participant.id,
                    'expense_id': expense.id,
                    'amount': split_amount,
                    'name': expense.name,
                })

class ExpenseSplit(models.Model):
    _name = 'expense.split'
    _description = 'Expense Split'

    name = fields.Char(string='Expense Name', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    expense_id = fields.Many2one('expense.expense', string='Expense', required=True, ondelete='cascade')
    amount = fields.Float(string='Amount', required=True)
    split_amount = fields.Float(string='Split Amount', readonly=True)
