# See LICENSE file for full copyright and licensing details.
from odoo import _, fields, models, api
from odoo.exceptions import ValidationError


class HotelHousekeeping(models.Model):
    _name = "hotel.housekeeping"
    _description = "Hotel Housekeeping"
    _rec_name = "room_id"

    current_date = fields.Date(
        "Today's Date",
        required=True,
        index=True,
        states={"done": [("readonly", True)]},
        default=fields.Date.today,
    )
    clean_type = fields.Selection(
        [
            ("daily", "Daily"),
            ("checkin", "Check-In"),
            ("checkout", "Check-Out"),
        ],
        "Clean Type",
        required=True,
        states={"done": [("readonly", True)]},
    )
    room_id = fields.Many2one(
        "hotel.room",
        "Room No",
        required=True,
        states={"done": [("readonly", True)]},
        index=True,
    )
    activity_line_ids = fields.One2many(
        "hotel.housekeeping.activities",
        "housekeeping_id",
        "Activities",
        states={"done": [("readonly", True)]},
        help="Detail of housekeeping \
                                        activities",
    )
    inspector_id = fields.Many2one(
        "res.users",
        "Inspector",
        required=True,
        states={"done": [("readonly", True)]},
    )
    inspect_date_time = fields.Datetime(
        "Inspect Date Time",
        required=True,
        states={"done": [("readonly", True)]},
    )
    quality = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("average", "Average"),
            ("bad", "Bad"),
            ("ok", "Ok"),
        ],
        "Quality",
        states={"done": [("readonly", True)]},
        help="Inspector inspect the room and mark \
                                as Excellent, Average, Bad, Good or Ok. ",
    )
    state = fields.Selection(
        [
            ("inspect", "Inspect"),
            ("dirty", "Dirty"),
            ("clean", "Clean"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        "State",
        states={"done": [("readonly", True)]},
        required=True,
        readonly=True,
        default="inspect",
    )

    res_id = fields.Many2one("hotel.reservation", "Ref No")

    housekeeping_cancel_remarks = fields.Text(string='Housekeeping Cancel Remarks')
    housekeeping_cancel_remarks_2 = fields.Text(string='Housekeeping Cancel Remarks')
    housekeeping_cancel_remarks_3 = fields.Text(string='Housekeeping Cancel Remarks')

    @api.onchange("res_id")
    def _onchange_of_res_id(self):
        for room in self.res_id.reservation_line:
            print('---------------------------------------------', room.name)
            self.write({
                'room_id': room.id,
            })

    def house_keeping_cancel(self):
        view_id = self.env['housekeeping.cancel']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hotel Management Table Order Cancel Remarks',
            'res_model': 'housekeeping.cancel',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('hotel_housekeeping.hotel_management_table_cancel_remarks_wizard', False).id,
            'target': 'new',
        }

    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "dirty", "quality": False})
        self.activity_line_ids.write({"is_clean": False, "is_dirty": True})

    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "cancel", "quality": False})

    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        if not self.quality:
            raise ValidationError(_("Alert!, Please update quality of work!"))
        folio_id = self.env["hotel.folio"].search([("reservation_id", "=", self.res_id.id)])
        if folio_id:
            line_vals = []
            vals = [0, 0, {
                "current_date": self.current_date,
                "clean_type": self.clean_type,
                "room_id": self.room_id.id,
                "inspector_id": self.inspector_id.id,
                "inspect_date_time": self.inspect_date_time,
            }]
            line_vals.append(vals)
        else:
            raise ValidationError(_("Alert!, Please Create a Folio against the Reservation"))
        folio_id.update({
            'hotel_house_keeping_orders_ids': line_vals,
        })
        self.write({"state": "done"})

    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "inspect", "quality": False})

    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "clean", "quality": False})
        self.activity_line_ids.write({"is_clean": True, "is_dirty": False})