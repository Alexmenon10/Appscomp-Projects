# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HotelReservationWizard(models.TransientModel):
    _name = "hotel.reservation.wizard"
    _description = "Allow to generate a reservation"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)

    def report_reservation_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }

        return self.env.ref("hotel_extended.hotel_roomres_details").report_action(
            self, data=data
        )

    def report_checkin_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }

        return self.env.ref("hotel_extended.hotel_checkin_details").report_action(
            self, data=data
        )

    #
    def report_checkout_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_extended.hotel_checkout_details").report_action(
            self, data=data
        )

    def report_maxroom_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_extended.hotel_maxroom_details").report_action(
            self, data=data
        )


class MakeFolioWizard(models.TransientModel):
    _name = "wizard.make.folio"
    _description = "Allow to generate the folio"

    grouped = fields.Boolean("Group the Folios")

    def make_folios(self):
        reservation_obj = self.env["hotel.reservation"]
        newinv = [
            order.id
            for order in reservation_obj.browse(
                self.env.context.get("active_ids", [])
            ).mapped("folio_id")
        ]
        return {
            "domain": "[('id','in', [" + ",".join(map(str, newinv)) + "])]",
            "name": "Folios",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "hotel.folio",
            "view_id": False,
            "type": "ir.actions.act_window",
        }


class NewQuickReservationWizard(models.TransientModel):
    _name = "new.quick.reservation.wizard"
    _description = "New Quick Reservation Wizard"

    name = fields.Char(string='Guest Name')
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string='E-mail')
    valid_proof = fields.Many2one("identity.register", "Proof Type")
    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High')],
        string='Priority')

