from odoo import api, fields, models


# class HotelFolio(models.Model):
#     _inherit = "hotel.folio"
#
#     state = fields.Selection(
#         [("draft", "Draft"),
#          ("confirm", "Confirm"),
#          ("cancel", "Cancel"),
#          ("done", "Done"), ],
#         "State",
#         readonly=True,
#         default="draft", )


class HotelFolio(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ],
        "State",
        readonly=True,
        default="draft")
