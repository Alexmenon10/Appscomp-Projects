# -*- coding: utf-8 -*-
import base64
import csv
from datetime import date

from odoo.exceptions import Warning,ValidationError
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import xlrd


# try:
#     import xlrd
# except ImportError:
#     _logger.debug('Cannot `import xlrd`.')


class AttendanceImportWizard(models.TransientModel):
    _name = 'attendance.import.wizard'
    _description = 'Attendance Import Wizard'

    data_file = fields.Binary(string='XLS File')
    file_name = fields.Char('Filename')

    def action_import(self, xlrd=None):
        if not self.data_file:
            raise ValidationError(_("Please Upload File to Import Employee !"))

        else:
            line = keys = ['emp_code', 'check_in', 'check_out']
            try:
                csv_data = base64.b64decode(self.data_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Please Select Valid File Format !"))

            values = {}
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        print('-*****************************************************************-',values)
                        res = self.create_employee(values)

    def create_employee(self, values):
        attendance = self.env['hr.attendance']
        active_id = self.env['import.manual.attendance'].browse(self.env.context.get('active_id'))
        line_vals=[]
        print('++++++++++++++++++++++++++++++++++++++++++++', active_id.name)
        # department_id = self.get_department(values.get('department_id'))
        # address_id = self.get_address(values.get('address_id'))
        # birthday = self.get_birthday(values.get('birthday'))
        #
        # if values.get('gender') == 'Male':
        #     gender = 'male'
        # elif values.get('gender') == 'male':
        #     gender = 'male'
        # elif values.get('gender') == 'Female':
        #     gender = 'female'
        # elif values.get('gender') == 'female':
        #     gender = 'female'
        # elif values.get('gender') == 'Other':
        #     gender = 'other'
        # elif values.get('gender') == 'other':
        #     gender = 'other'
        # else:
        #     gender = 'male'

        vals = {
            'emp_code': values.get('emp_code'),
            'check_in': values.get('check_in'),
            'check_out': values.get('check_out'),
            # 'work_phone': values.get('work_phone'),
            # 'work_email': values.get('work_email'),
            # 'department_id': department_id.id,
            # 'address_id': address_id.id,
            # 'gender': gender,
            # 'birthday': birthday,
        }
        # valsss = {
        #     'date': date.today()
        # }
        # print('*------------------------------------------------------------------------------*', vals,date.todday())
        if values.get('name') == '':
            raise ValidationError(_('Employee Name is Required !'))
        line_vals.append((0, 0, vals))
        active_id.import_ids = line_vals
        # if values.get('department_id') == '':
        #     raise ValidationError(_('Department Field can not be Empty !'))
        # res = active_id.import_ids.append(vals)
        # return res

        #
        # active_id = self.env['import.manual.attendance'].browse(self.env.context.get('active_id'))
        # bom_line = self.env['import.attendance']
        # for mrp_bom_line in active_id:
        #     if not self.file_name:
        #         print("no file found")
        #         return False
        #     if self.file_name:
        #         print('******************************1.5*****************************', )
        #         try:
        #             fp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        #             fp.write(binascii.a2b_base64(self.data_file))
        #             print('******************************1.6*****************************', fp)
        #             fp.seek(0)
        #             workbook = xlrd.open_workbook(fp.name)
        #             sheet = workbook.sheet_by_index(0)
        #         except Exception:
        #             raise exceptions.Warning(_("Invalid file!"))
        #     else:
        #         print('***********************************************************', )
        #     reader = []
        #     keys = sheet.row_values(0)
        #     values = [sheet.row_values(i) for i in range(1, sheet.nrows)]
        #     print('****************************1.1*******************************', )
        #     for value in values:
        #         reader.append(dict(zip(keys, value)))
        #         print('******************************1.2*****************************', reader)
        #     for line in reader:
        #         active_ids = self.env['import.manual.attendance'].browse(self.env.context.get('active_id'))
        #         vals = {
        #             # 'bom_id': active_ids.id,
        #             # 'product_id': int(line.get('product_id')),
        #             # 'product_qty': line.get('product_qty')
        #         }
        #         bom_line |= self.env['import.attendance'].create(vals)
        # return True


class AttendanceBulkWizard(models.TransientModel):
    _name = 'attendance.bulk.wizard'
    _description = 'Attendance Bulk Wizard'

    employee_ids = fields.Many2many('hr.employee', string='Employee')

    def action_bulk_attendance(self):
        print('+++++++++++++++++++')

