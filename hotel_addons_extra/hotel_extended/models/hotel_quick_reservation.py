# See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one(
        "res.partner",
        string="Guest"
    )
    check_in = fields.Datetime("Check In")
    check_out = fields.Datetime("Check Out")
    room_id = fields.Many2one(
        "hotel.room",
        string="Room"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Hotel",
        default=lambda self: self.env.company
    )
    guest_type = fields.Selection(
        [("individual", "Individual"),
         ("company", "Company")],
        string="Guest Type",
        default='individual'
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist"
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Invoice Address"
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        string="Ordering Contact"
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        string="Delivery Address"
    )
    room_image = fields.Binary(
        string='Room Image',
        related='room_id.image_1920'
    )
    adults = fields.Integer("Adults")
    guest_creation = fields.Selection(
        [("exist", "Exist"),
         ("new", "New")],
        string="Guest Status",
        default='new'
    )
    room_amenities_ids = fields.Many2many(
        "hotel.room.amenities",
        string="Room Amenities",
        help="List of room amenities.",
        related='room_id.room_amenities_ids'
    )
    name = fields.Char(string='Guest Name')
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string='E-mail')
    valid_proof = fields.Many2one(
        "identity.register",
        string="Proof Type"
    )
    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High')],
        string='Priority')
    create_guest = fields.Boolean(
        string='Do You Want to Generate a New Guest...?'
    )

    def test_code(self):
        pass

    @api.onchange("check_out", "check_in")
    def _on_change_check_out(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if (self.check_out and self.check_in) and (self.check_out < self.check_in):
            raise ValidationError(
                _("Checkout date should be greater than Checkin date.")
            )

    @api.onchange("partner_id")
    def _onchange_partner_id_res(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        res = super(QuickRoomReservation, self).default_get(fields)
        keys = self._context.keys()
        if "date" in keys:
            res.update({"check_in": self._context["date"]})
        if "room_id" in keys:
            roomid = self._context["room_id"]
            res.update({"room_id": int(roomid)})
        return res

    #
    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env["hotel.reservation"]
        for res in self:
            rec = hotel_res_obj.create(
                {
                    "partner_id": res.partner_id.id,
                    "partner_invoice_id": res.partner_invoice_id.id,
                    "partner_order_id": res.partner_order_id.id,
                    "partner_shipping_id": res.partner_shipping_id.id,
                    "checkin": res.check_in,
                    "checkout": res.check_out,
                    "company_id": res.company_id.id,
                    "pricelist_id": res.pricelist_id.id,
                    "adults": res.adults,
                    "state": 'confirm',
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, res.room_id.ids)],
                                "name": res.room_id.name or " ",
                            },
                        )
                    ],
                }
            )
            hotel_res_obj_new= self.env["hotel.reservation"].search([
                ("partner_id", "=", res.partner_id.id),
                ("checkin", "=", res.check_in),
                ("checkout", "=", res.check_out),
                ("adults", "=", res.adults),
                # ("reservation_line.name", "=", res.room_id.name),
            ])
            vals = {
                "room_id": res.room_id.id,
                "check_in": res.check_in,
                "check_out": res.check_out,
                "state": "assigned",
                "status": "confirm",
                "reservation_id": hotel_res_obj_new.id,
            }
            self.env["hotel.room.reservation.line"].create(vals)
        return rec

    @api.onchange('create_guest')
    def create_new_guest(self):
        for val in self:
            if val.name and val.create_guest:
                values = {
                    'name': val.name,
                    # 'company_type': val.guest_type,
                }
                self.env['res.partner'].sudo().create(values)
                partner = self.env['res.partner'].sudo().search([
                    ('name', '=', self.name)])
                self.write({
                    'guest_creation': 'exist',
                    'partner_id': partner.id,
                })
