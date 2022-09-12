import logging
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)
try:
    import pytz
except (ImportError, IOError) as err:
    _logger.debug(err)


class ChooseSummary(models.Model):
    _name = "choose.summary"
    _description = "Choose Based Room Summary"

    name = fields.Char(string="Chose Summary")
    image = fields.Binary(string="Image")

    # def time_based_reserve(self):
    #     print("Time =================================")
    #
    # def date_based_reserve(self):
    #     print("Date =============================")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            result.append((rec.id, name))
        return result


class TimeBasedRoomReserve(models.Model):
    _name = "time.based.room.reserve"
    _description = "Time Based RoomReserve"

    name = fields.Char("Reservation Summary", default="Reservations Summary")
    date_from = fields.Datetime("Date From", default=lambda self: fields.Date.today())
    date_to = fields.Datetime(
        "Date To",
        default=lambda self: fields.Date.today() + relativedelta(days=30),
    )
    room_categ_id = fields.Many2many(
        "hotel.floor", string="Floor Category", ondelete="restrict"
    )
    room_category = fields.Many2many("hotel.room.type", string="Room Category")

    summary_header = fields.Text("Summary Header")
    room_summary = fields.Text("Room Summary")
    date_today = fields.Date("Date", default=lambda self: fields.Date.today())
    time_interval = fields.Char('Time Interval')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            result.append((rec.id, name))
        return result

    def room_reservation(self):
        """room_line_ids
        @param self: object pointer
        """
        resource_id = self.env.ref("hotel_extended.view_hotel_reservation_form").id
        return {
            "name": _("Reconcile Write-Off"),
            "context": self._context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hotel.reservation",
            "views": [(resource_id, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.onchange("date_today", "room_categ_id", "room_category", "time_interval")  # noqa C901 (function is too complex)
    def get_room_summary_for_day(self):  # noqa C901 (function is too complex)
        import datetime
        start = "00:00:00"
        end = "23:59:59"
        delta = datetime.timedelta(minutes=int(self.time_interval))
        start = datetime.datetime.strptime(start, '%H:%M:%S')
        end = datetime.datetime.strptime(end, '%H:%M:%S')
        t = start
        summary_header_list = []
        if self.time_interval:
            while t <= end:
                interval = datetime.datetime.strftime(t, '%H:%M:%S')
                print(interval)
                summary_header_list.append(interval)
                t += delta
        global reserve_checkin_date, reserve_checkout_date
        hours = [(n, "%d %s" % (n % 12 or 12, ["AM", "PM"][n > 11])) for n in range(24)]
        res = {}
        all_detail = []
        main_header = []
        all_room_detail = []
        domain = [('check_in', '=', self.date_today), ('check_out', '=', self.date_today)]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        room_obj = self.env["hotel.room"]
        if not self.time_interval:
            for time in hours:
                summary_header_list.append(time[1])
        domain = []

        if self.room_categ_id:
            domain = [('floor_id', '=', self.room_categ_id.ids)]
        elif self.room_category:
            domain = [('room_categ_id', '=', self.room_category.ids)]
        if self.date_today or self.room_categ_id or self.room_category:
            print('*********************success')
            room_ids = room_obj.search(domain)
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                chk_date = self.date_today
                room_detail.update({"name": room.name or ""})
                if room.room_reservation_line_ids:
                    reserline_ids = room.room_reservation_line_ids.ids
                    reservline_ids = reservation_line_obj.search(
                        [
                            ("id", "in", reserline_ids),
                            ("state", "=", "assigned"),
                        ]
                    )
                    for reserve_val in room.room_reservation_line_ids:
                        reserve_checkin = reserve_val.check_in + timedelta(hours=5, minutes=30)
                        reserve_checkout = reserve_val.check_out + timedelta(hours=5, minutes=30)
                        reserve_checkin_date = reserve_checkin.date()
                        reserve_checkin_time = reserve_checkin.time()
                        reserve_checkout_date = reserve_checkout.date()
                        reserve_checkout_time = reserve_checkout.time()
                        if chk_date == reserve_checkin_date and chk_date == reserve_checkout_date:
                            for entry in summary_header_list:
                                if self.time_interval:
                                    reserve_checkin_time = str(reserve_checkin_time).split(':')[0]
                                    reserve_checkout_time = str(reserve_checkout_time).split(':')[0]
                                    if reserve_checkin_time <= entry <= reserve_checkout_time:
                                        room_list_stats.append(
                                            {
                                                "state": "Reserved",
                                                "date": str(chk_date),
                                                "room_id": room.id,
                                                "is_draft": "No",
                                                "data_model": "",
                                                "data_id": 0,
                                            }
                                        )
                                    else:
                                        room_list_stats.append(
                                            {
                                                "state": "Free",
                                                "date": str(chk_date),
                                                "room_id": room.id,
                                                "entry": entry,
                                            }
                                        )
                                else:
                                    m2 = datetime.strptime(entry, '%I %p')
                                    m3 = str(m2).split(':')[0].split(' ')[-1]
                                    reserve_checkin_time = str(reserve_checkin_time).split(':')[0]
                                    reserve_checkout_time = str(reserve_checkout_time).split(':')[0]
                                    if reserve_checkin_time <= m3 <= reserve_checkout_time:
                                        room_list_stats.append(
                                            {
                                                "state": "Reserved",
                                                "date": str(chk_date),
                                                "room_id": room.id,
                                                "is_draft": "No",
                                                "data_model": "",
                                                "data_id": 0,
                                            }
                                        )
                                    else:
                                        room_list_stats.append(
                                            {
                                                "state": "Free",
                                                "date": str(chk_date),
                                                "room_id": room.id,
                                                "entry": m3 + ':' + '00',
                                            }
                                        )
                            break
                        else:
                            for entry in summary_header_list:
                                import datetime
                                if not self.time_interval:
                                    m2 = datetime.datetime.strptime(entry, '%I %p')
                                    m3 = str(m2).split(':')[0].split(' ')[-1]
                                    room_list_stats.append(
                                        {
                                            "state": "Free",
                                            "date": str(chk_date),
                                            "room_id": room.id,
                                            "entry": m3 + ':' + '00',
                                        }
                                    )
                                else:
                                    room_list_stats.append(
                                        {
                                            "state": "Free",
                                            "date": str(chk_date),
                                            "room_id": room.id,
                                            "entry": entry,
                                        }
                                    )
                            break

                if not room.room_reservation_line_ids:
                    for entry in summary_header_list:
                        import datetime
                        if self.time_interval:
                            room_list_stats.append(
                                {
                                    "state": "Free",
                                    "date": str(chk_date),
                                    "room_id": room.id,
                                    "entry": entry,
                                }
                            )
                        else:
                            m2 = datetime.datetime.strptime(entry, '%I %p')
                            m3 = str(m2).split(':')[0].split(' ')[-1]
                            room_list_stats.append(
                                {
                                    "state": "Free",
                                    "date": str(chk_date),
                                    "room_id": room.id,
                                    "entry": entry,
                                }
                            )

                # else:
                #     for entry in summary_header_list:
                #         m2 = datetime.strptime(entry, '%I %p')
                #         m3 = str(m2).split(':')[0].split(' ')[-1]
                #         room_list_stats.append(
                #             {
                #                 "state": "Free",
                #                 "date": str(chk_date),
                #                 "room_id": room.id,
                #                 "entry": m3 + ':' + '00',
                #             }
                #         )
                # if not chk_date == reserve_checkin_date and not chk_date == reserve_checkout_date:
                #     for entry in summary_header_list:
                #         m2 = datetime.strptime(entry, '%I %p')
                #         m3 = str(m2).split(':')[0].split(' ')[-1]
                #         room_list_stats.append(
                #             {
                #                 "state": "Free",
                #                 "date": str(chk_date),
                #                 "room_id": room.id,
                #                 "entry": m3 + ':' + '00',
                #             }
                #         )

                room_detail.update({"value": room_list_stats})
                all_room_detail.append(room_detail)
        summary_header_list.insert(0, "Rooms")
        main_header.append({"header": summary_header_list})
        self.summary_header = str(main_header)
        self.room_summary = str(all_room_detail)
        return res

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            result.append((rec.id, name))
        return result