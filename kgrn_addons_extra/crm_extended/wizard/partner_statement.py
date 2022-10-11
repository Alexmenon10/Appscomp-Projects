from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
import datetime
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import pdb

MONTH_LIST = [('1', 'Jan'), ('2', 'Feb'), ('3', 'Mar'),
              ('4', 'Apr'), ('5', 'May'), ('6', 'Jun'),
              ('7', 'Jul'), ('8', 'Aug'), ('9', 'Sep'),
              ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')]


class PartnerStatementReport(models.TransientModel):
    _name = 'wizard.partner.statement'
    _description = 'Partner Statement Excel Report'

    def _get_startdate(self):
        fiscalyear_last_date = 31
        fiscalyear_last_month = 3
        # pdb.set_trace()
        current_year = datetime.now().strftime('%Y')
        current_month = datetime.now().strftime('%m')
        current_date = fields.Datetime.now()
        start_date = datetime(int(current_year), int(current_month), int(1))
        return start_date

    summary_file = fields.Binary('Partner Statement')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Partner Statement Report Printed')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    start_date = fields.Date("Start Date", default=_get_startdate)
    end_date = fields.Date("End Date", default=fields.Datetime.now())
    report_type = fields.Selection([
        ('ledger', 'Ledger Statement'),
        ('outstanding', 'Outstanding Report')
    ], string='Report Type', default='ledger')

    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_id')
        res = super(PartnerStatementReport, self).default_get(fields)
        partner = self.env['res.partner'].browse(record_ids)
        res.update({'partner_id': partner.id})
        return res

    def get_partner_report(self):
        for record in self:
            if record.report_type == 'ledger':
                res = record.sudo().action_get_partner_statement_report_excel()
            elif record.report_type == 'outstanding':
                res = record.sudo().action_get_partner_outstanding_statement_report_excel()
            return res

    def action_get_partner_statement_report_excel(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('%s' % (self.partner_id.display_name))

        design_7 = easyxf('align: horiz left;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;')
        design_14 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_15 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_16 = easyxf('align: horiz right;font: bold 1;pattern: pattern solid, fore_colour gray25;')



        style2 = xlwt.XFStyle()
        style2.num_format_str = '#,##0.00'
        style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

        worksheet1.col(0).width = 2000
        worksheet1.col(1).width = 3000
        worksheet1.col(2).width = 5000
        worksheet1.col(3).width = 10500
        worksheet1.col(4).width = 8000
        worksheet1.col(5).width = 8000
        worksheet1.col(6).width = 3000
        worksheet1.col(7).width = 3000
        worksheet1.col(8).width = 4500
        worksheet1.col(9).width = 4500
        worksheet1.col(10).width = 3000
        worksheet1.col(11).width = 4500
        worksheet1.col(12).width = 4500
        worksheet1.col(13).width = 8500
        worksheet1.col(14).width = 6500

        rows = 6
        cols = 0
        row_pq = 6
        import datetime
        date3 = str(self.start_date)
        date4 = datetime.datetime.strptime(date3, '%Y-%m-%d')
        date5 = date4.strftime("%d/%m/%Y")
        date6 = str(self.end_date)
        date7 = datetime.datetime.strptime(date6, '%Y-%m-%d')
        date8 = date7.strftime("%d/%m/%Y")
        worksheet1.write_merge(0, 0, 0, 5, 'Customer - %s' % (self.partner_id.display_name), design_14)
        address = ''
        if self.partner_id.street:
            address += str(self.partner_id.street) + ' '
        if self.partner_id.street2:
            address += str(self.partner_id.street2) + ' '
        if self.partner_id.city:
            address += str(self.partner_id.city) + ' '
        if self.partner_id.state_id.display_name:
            address += str(self.partner_id.state_id.display_name) + ' '
        if self.partner_id.zip:
            address += str(self.partner_id.zip) + ' '
        if self.partner_id.country_id.display_name:
            address += str(self.partner_id.country_id.display_name)
        worksheet1.write_merge(1, 1, 0, 5, 'Address - %s' % (address), design_7)
        if self.start_date and self.end_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement from : %s till %s' % (date5, date8),
                                   design_7)
        if self.start_date and not self.end_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement from : %s ' % (date5), design_7)
        if self.end_date and not self.start_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement till %s ' % (date8), design_7)

        ##  Opening Balance Starts  ###
        from dateutil.parser import parse
        date9 = parse(str(self.start_date))
        date10 = parse(str(self.end_date))
        date11 = parse(str(date9)) - timedelta(days=1)
        domain2 = [('account_id.internal_type', 'in', ['receivable', 'payable']), ('date', '<=', date11), \
                   ('move_id.state', '=', 'posted'),
                   ('partner_id', '=', self.partner_id.id)]
        cr_dr_lines2 = self.env['account.move.line'].sudo().search(domain2)
        currency_line = self.env['account.move.line'].sudo().search(domain2, limit=1)
        # currency_id =currency_line.journal_id.company_id.currency_id.display_name
        # company_id1 = self.env['res.company']
        # currency_id = company_id1.currency_id.display_name
        op_balance = 0
        for move_line2 in cr_dr_lines2:
            op_balance += (move_line2.debit - move_line2.credit)
        # pdb.set_trace()
        op_balance = round(op_balance, 2)
        opening_balance = str('%.2f' % op_balance)
        worksheet1.write_merge(3, 3, 0, 5, 'Opening Balance : %s' % (opening_balance), design_15)
        ##  Opening Balance Ends  ###
        closing_balance = 0
        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0

        worksheet1.write(rows, col_1, _('Sl.No'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Date'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Invoice No.'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Ledger Name'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Label'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Journal'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Debit'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Credit'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Amount Residual'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Closing Balance'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Due On'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Overdue by Days'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Reference'), design_14)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1
        for record in self:
            domain = [('partner_id', '=', record.partner_id.id),
                      ('move_id.state', '=', 'posted'),
                      ('account_id.internal_type', 'in', ['receivable', 'payable'])]
            if record.start_date:
                domain += [('date', '>=', record.start_date)]
            if record.end_date:
                domain += [('date', '<=', record.end_date)]
            invoice_lines = self.env['account.move.line'].sudo().search(domain, order='date asc, id asc')
            r_1 = 0
            if len(invoice_lines) == 0:
                closing_balance += op_balance
            for line in invoice_lines:
                invoice_due_date = ''
                ref_date1 = line.date
                due_date = line.date_maturity
                import datetime
                d11 = str(ref_date1)
                dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d')
                date1 = dt21.strftime("%d/%m/%Y")
                due_day = 0
                overdue_days = 0
                if due_date:
                    d22 = str(due_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
                    invoice_due_date = dt22.strftime("%d/%m/%Y")
                    date_maturity = line.date_maturity
                    today = datetime.datetime.today().date()
                    overdue_days = (today - date_maturity).days
                worksheet1.write(row_pq, 0, sl_no, design_8)
                worksheet1.write(row_pq, 1, date1, design_8)
                worksheet1.write(row_pq, 2, line.move_name, design_8)
                worksheet1.write(row_pq, 3, line.account_id.name, design_8)
                if line.name:
                    worksheet1.write(row_pq, 4, line.name, design_8)
                else:
                    worksheet1.write(row_pq, 4, '', design_8)
                worksheet1.write(row_pq, 5, line.journal_id.name, design_8)
                worksheet1.write(row_pq, 6, round(line.debit, 2), style2)
                worksheet1.write(row_pq, 7, round(line.credit, 2), style2)
                worksheet1.write(row_pq, 8, round(line.amount_residual, 2), style2)
                if r_1 == 0:
                    closing_balance += op_balance + line.debit - line.credit
                    r_1 += 1
                elif r_1 == 1:
                    closing_balance += line.debit - line.credit
                # pdb.set_trace()
                worksheet1.write(row_pq, 9, round(closing_balance, 2), style2)
                worksheet1.write(row_pq, 10, invoice_due_date, design_8)
                worksheet1.write(row_pq, 11, overdue_days, design_8)
                if line.ref:
                    worksheet1.write(row_pq, 12, line.ref, design_8)
                sl_no += 1
                row_pq += 1
            closing_balance1 = str('%.2f' % closing_balance)
            worksheet1.write_merge(row_pq, row_pq, 0, 9, 'Closing Balance till %s is %s' % (date8, closing_balance1),
                                   design_16)

        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({
            'summary_file': excel_file,
            'file_name': 'Statement Report-%s.xls' % self.partner_id.display_name,
            'report_printed': True,
        })
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'wizard.partner.statement',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }

    def action_get_partner_outstanding_statement_report_excel(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('%s' % (self.partner_id.display_name))

        design_7 = easyxf('align: horiz left;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;')
        design_14 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_15 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_16 = easyxf('align: horiz right;font: bold 1;pattern: pattern solid, fore_colour gray25;')



        style2 = xlwt.XFStyle()
        style2.num_format_str = '#,##0.00'

        worksheet1.col(0).width = 2000
        worksheet1.col(1).width = 3000
        worksheet1.col(2).width = 5000
        worksheet1.col(3).width = 10500
        worksheet1.col(4).width = 8000
        worksheet1.col(5).width = 8000
        worksheet1.col(6).width = 4500
        worksheet1.col(7).width = 3000
        worksheet1.col(8).width = 4500
        worksheet1.col(9).width = 4500
        worksheet1.col(10).width = 3000
        worksheet1.col(11).width = 4500
        worksheet1.col(12).width = 5500
        worksheet1.col(13).width = 4500
        worksheet1.col(14).width = 4500
        worksheet1.col(15).width = 4500
        worksheet1.col(16).width = 4500
        worksheet1.col(17).width = 9500
        worksheet1.col(18).width = 9500

        rows = 6
        cols = 0
        row_pq = 6
        import datetime
        date3 = str(self.start_date)
        date4 = datetime.datetime.strptime(date3, '%Y-%m-%d')
        date5 = date4.strftime("%d/%m/%Y")
        date6 = str(self.end_date)
        date7 = datetime.datetime.strptime(date6, '%Y-%m-%d')
        date8 = date7.strftime("%d/%m/%Y")
        worksheet1.write_merge(0, 0, 0, 5, 'Customer - %s' % (self.partner_id.display_name), design_14)
        address = ''
        if self.partner_id.street:
            address += str(self.partner_id.street) + ' '
        if self.partner_id.street2:
            address += str(self.partner_id.street2) + ' '
        if self.partner_id.city:
            address += str(self.partner_id.city) + ' '
        if self.partner_id.state_id.display_name:
            address += str(self.partner_id.state_id.display_name) + ' '
        if self.partner_id.zip:
            address += str(self.partner_id.zip) + ' '
        if self.partner_id.country_id.display_name:
            address += str(self.partner_id.country_id.display_name)
        worksheet1.write_merge(1, 1, 0, 5, 'Address - %s' % (address), design_7)
        if self.start_date and self.end_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement from : %s till %s' % (date5, date8),
                                   design_7)
        if self.start_date and not self.end_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement from : %s ' % (date5), design_7)
        if self.end_date and not self.start_date:
            worksheet1.write_merge(2, 2, 0, 5, 'Statement till %s ' % (date8), design_7)

        ##  Opening Balance Starts  ###
        from dateutil.parser import parse
        date9 = parse(str(self.start_date))
        date10 = parse(str(self.end_date))
        date11 = parse(str(date9)) - timedelta(days=1)
        domain2 = [('account_id.internal_type', 'in', ['receivable', 'payable']),
                   ('date', '<=', date11), ('move_id.state', '=', 'posted'), ('partner_id', '=', self.partner_id.id)]

        cr_dr_lines2 = self.env['account.move.line'].search(domain2)
        currency_line = self.env['account.move.line'].search(domain2, limit=1)
        company_id1 = self.env.user.company_id
        currency_id = company_id1.currency_id.display_name
        op_balance = 0
        for move_line2 in cr_dr_lines2:
            op_balance += move_line2.balance
        op_balance = round(op_balance, 2)
        opening_balance = str('%.2f' % op_balance) + ' ' + currency_id
        worksheet1.write_merge(3, 3, 0, 5, 'Opening Balance : %s' % (opening_balance), design_15)
        ##  Opening Balance Ends  ###
        closing_balance = 0
        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0

        worksheet1.write(rows, col_1, _('Sl.No'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Date'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Invoice No.'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Ledger Name'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Label'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Journal'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Invoice Amount'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Reconciled'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Amount Residual'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Closing Balance'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Due On'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Overdue by Days'), design_14)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Reference'), design_14)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1
        for record in self:
            # domain = [('partner_id', '=', record.partner_id.id),
            #     ('move_id.state', '=', 'posted'),('amount_residual', '!=', 0),
            #     ('account_id.internal_type', 'in', ['receivable', 'payable'])]
            domain = [('partner_id', '=', record.partner_id.id),
                      ('move_id.state', '=', 'posted'),
                      ('account_id.internal_type', 'in', ['receivable', 'payable'])]
            if record.start_date:
                domain += [('date', '>=', record.start_date)]
            if record.end_date:
                domain += [('date', '<=', record.end_date)]
            # if record.branch_ids:
            #     domain += [('move_id.branch_id', 'in', record.branch_ids.ids)]
            invoice_lines = self.env['account.move.line'].sudo().search(domain, order='date asc, id asc')
            r_1 = 0
            if len(invoice_lines) == 0:
                closing_balance += op_balance
            # pdb.set_trace()
            for line in invoice_lines:
                domain_r = ['|', ('debit_move_id', '=', line.id), ('credit_move_id', '=', line.id)]
                reconciled_ids = self.env['account.partial.reconcile'].sudo().search(domain_r)
                reconciled_amt = 0
                state_list = []
                payment_id_r2 = ''
                for item in reconciled_ids:
                    if item.credit_move_id.id == line.id:
                        payment_id_r2 = item.debit_move_id.payment_id
                    elif item.debit_move_id.id == line.id:
                        payment_id_r2 = item.credit_move_id.payment_id
                    domain_pdc_r2 = [('payment_id', '=', payment_id_r2.id)]
                #     pdc_id_r2 = self.env['post.dated.cheques'].sudo().search(domain_pdc_r2)
                #     if pdc_id_r2:
                #         state_list.append(pdc_id_r2.state)
                # if state_list != []:
                #     if all('done' in s for s in state_list) and line.full_reconcile_id:
                #         continue
                # if state_list ==[]:
                #     if line.full_reconcile_id:
                #         continue
                # # pdb.set_trace()
                payment_id_r = ''
                pdc_id_r = ''
                for item in reconciled_ids:
                    reconciled_amt += item.amount
                # pdb.set_trace()
                ref_date1 = line.date
                due_date = line.date_maturity
                import datetime
                d11 = str(ref_date1)
                dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d')
                date1 = dt21.strftime("%d/%m/%Y")
                due_day = 0
                overdue_days = 0
                if due_date:
                    d22 = str(due_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
                    invoice_due_date = dt22.strftime("%d/%m/%Y")
                    date_maturity = line.date_maturity
                    today = datetime.datetime.today().date()
                    overdue_days = (today - date_maturity).days
                worksheet1.write(row_pq, 0, sl_no, design_8)
                worksheet1.write(row_pq, 1, date1, design_8)
                worksheet1.write(row_pq, 2, line.move_name, design_8)
                worksheet1.write(row_pq, 3, line.account_id.name, design_8)
                if line.name:
                    worksheet1.write(row_pq, 4, line.name, design_8)
                else:
                    worksheet1.write(row_pq, 4, '', design_8)
                worksheet1.write(row_pq, 5, line.journal_id.name, design_8)
                amount_1 = line.debit if line.debit > 0 else line.credit
                worksheet1.write(row_pq, 6, amount_1, style2)
                # worksheet1.write(row_pq, 6, line.move_id.amount_total, design_9)
                worksheet1.write(row_pq, 7, round(reconciled_amt, 2), style2)
                worksheet1.write(row_pq, 8, round(line.amount_residual, 2), style2)
                # worksheet1.write(row_pq, 8, line.move_id.amount_residual, design_9)
                if r_1 == 0:
                    closing_balance += op_balance + line.amount_residual
                    r_1 += 1
                elif r_1 == 1:
                    closing_balance += line.amount_residual
                worksheet1.write(row_pq, 9, round(closing_balance, 2), style2)
                worksheet1.write(row_pq, 10, invoice_due_date, design_8)
                worksheet1.write(row_pq, 11, overdue_days, design_8)
                if line.ref:
                    worksheet1.write(row_pq, 12, line.ref, design_8)
                for item in reconciled_ids:
                    reconciled_amt += item.amount
                    if item.credit_move_id.id == line.id:
                        payment_id_r = item.debit_move_id.payment_id
                    elif item.debit_move_id.id == line.id:
                        payment_id_r = item.credit_move_id.payment_id
                    reconciled_amt23 = 0
                    # row_pq+=1
                    # worksheet1.write(row_pq, 17, line.move_id.branch_id.display_name, design_8)
                    # worksheet1.write(row_pq, 18, line.company_id.display_name, design_8)
                    sl_no += 1
                    row_pq += 1
            closing_balance1 = str('%.2f'%closing_balance)
            worksheet1.write_merge(row_pq, row_pq, 0, 9, 'Closing Balance till %s is %s' % (date8,closing_balance1), design_16)

        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({
            'summary_file': excel_file,
            'file_name': 'Outstanding Statement Report-%s.xls' % self.partner_id.display_name,
            'report_printed': True,
        })
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'wizard.partner.statement',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }



