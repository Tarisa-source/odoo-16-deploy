from odoo import models, fields, api, exceptions
from datetime import datetime as dt, time
import pytz
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomAttendance(models.Model):
    _name = 'attendance.machine'
    _description = 'Custom Attendance Data'

    scan_date = fields.Datetime(string='Tanggal Scan', required=True)
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')
    date = fields.Date(string='Tanggal', store=True)
    time = fields.Char(string='Jam', store=True)
    pin = fields.Char(string='PIN', required=True)
    nip = fields.Char(string='NIP', required=True)
    name = fields.Char(string='Nama', required=True)
    division = fields.Char(string='Divisi', required=True)
    resource = fields.Char(string='Resource', required=True)
    placement = fields.Char(string='Penempatan', required=True)
    verification = fields.Char(string='Verifikasi', required=True)
    io = fields.Char(string='I/O', required=True)
    workcode = fields.Char(string='Workcode', required=True)
    sn = fields.Char(string='SN', required=True)
    machine = fields.Char(string='Mesin', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')  # Field relasi ke hr.employee

    @api.model
    def process_attendance_records(self):
        records = self.search([])

        attendance_dict = {}

        for record in records:
            date = record.date
            name = record.name
            scan_time = record.scan_date
            key = (name, date)

            if key not in attendance_dict:
                attendance_dict[key] = {'check_in': None, 'check_out': None}

            if not attendance_dict[key]['check_in'] or scan_time < attendance_dict[key]['check_in']:
                attendance_dict[key]['check_in'] = scan_time
            elif not attendance_dict[key]['check_out'] or scan_time > attendance_dict[key]['check_out']:
                attendance_dict[key]['check_out'] = scan_time

        for key, times in attendance_dict.items():
            name, date = key
            check_in_time = times['check_in']
            check_out_time = times['check_out']

            record = self.search([('name', '=', name), ('date', '=', date)], limit=1)

            if record:
                record.write({
                    'check_in': check_in_time,
                    'check_out': check_out_time,
                })

        # Menghapus record yang memiliki nilai check_in dan check_out sebagai null
        records_to_delete = self.search([('check_in', '=', False), ('check_out', '=', False)])
        records_to_delete.unlink()

        # Mengisi check_out yang bernilai null dengan data check_in, namun dengan jam 23:00:00 pada tanggal yang sama
        records_to_update = self.search([('check_out', '=', False), ('check_in', '!=', False)])
        for record in records_to_update:
            utc_check_in = record.check_in
            wib_tz = pytz.timezone('Asia/Jakarta')

            # Konversi check_in ke zona waktu WIB hanya jika belum memiliki tzinfo
            if utc_check_in.tzinfo is None:
                wib_check_in = utc_check_in.replace(tzinfo=pytz.utc).astimezone(wib_tz)
            else:
                wib_check_in = utc_check_in.astimezone(wib_tz)

            # Set check_out time to 23:00 WIB pada tanggal yang sama
            wib_check_out = wib_check_in.replace(hour=23, minute=0, second=0, microsecond=0)

            # Konversi check_out kembali ke UTC
            utc_check_out = wib_check_out.astimezone(pytz.utc).replace(tzinfo=None)

            record.write({
                'check_out': utc_check_out,
            })

        # Memindahkan data ke hr.attendance
        for record in self.search([('check_in', '!=', False), ('check_out', '!=', False)]):
            employee = self.env['hr.employee'].search([('name', '=', record.name)], limit=1)
            if employee:
                # Cek jika ada data dengan nama dan tanggal yang sama
                existing_attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', record.check_in),
                    ('check_in', '<=', record.check_in)
                ])
                if not existing_attendance:
                    try:
                        self.env['hr.attendance'].create({
                            'employee_id': employee.id,
                            'check_in': record.check_in,
                            'check_out': record.check_out,
                        })
                        _logger.info(f"Created hr.attendance for employee {employee.name} on {record.check_in.date()}")
                    except ValidationError as e:
                        _logger.warning(f"Validation error for employee {record.name}: {e}")
                else:
                    _logger.info(f"Attendance already exists for employee {record.name} on {record.check_in.date()}")


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    shift = fields.Selection([
        ('Shift 1', 'Shift 1'),
        ('Shift 2', 'Shift 2'),
        ('Shift 3', 'Shift 3')
    ], string='Shift', compute='_compute_shift', store=True)

    @api.depends('check_in')
    def _compute_shift(self):
        for record in self:
            record.shift = self.get_shift(record.check_in)

    def get_shift(self, check_in):
        # Tentukan zona waktu lokal (WIB)
        wib_tz = pytz.timezone('Asia/Jakarta')

        if check_in:
            check_in_time = check_in.astimezone(wib_tz).time()
            if time(0, 0) <= check_in_time < time(8, 0):
                return 'Shift 1'
            elif time(8, 0) <= check_in_time < time(16, 0):
                return 'Shift 2'
            else:
                return 'Shift 3'
        return False

    @api.model
    def create(self, vals):
        # Supaya tidak terjadi recursion, tambahkan context flag
        if not self.env.context.get('skip_shift_update'):
            vals['shift'] = self.get_shift(vals.get('check_in'))
        return super(Attendance, self).create(vals)

    def write(self, vals):
        # Supaya tidak terjadi recursion, tambahkan context flag
        if not self.env.context.get('skip_shift_update'):
            # Buat context baru dengan flag
            new_context = dict(self.env.context, skip_shift_update=True)
            for record in self:
                shift = self.get_shift(vals.get('check_in', record.check_in))
                vals['shift'] = shift
                # Gunakan context baru untuk memanggil write
                super(Attendance, record.with_context(new_context)).write(vals)
        else:
            super(Attendance, self).write(vals)
        return True
