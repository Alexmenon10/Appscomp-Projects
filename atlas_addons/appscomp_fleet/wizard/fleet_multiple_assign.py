from odoo import fields, models, api


class FleetMultipleAssign(models.Model):
    _name = 'fleet.multiple.assign'
    _description = 'Fleet Multiple Assign'

    name = fields.Char()

    vehicle_category = fields.Selection([
        ("car", "Car"),
        ("bike", "Bike"),
        ("bus", "Bus"),
        ("jcb", "JCB"),
        ("tractor", "Tractor"),
        ("jeep", "Jeep"),
        ("tanker_lorry", "Tanker Lorry"),
        ("tipper_lorry", "Tipper Lorry"),
        ("load_vehicle", "Load Vehicle"),
    ], string='Vehicle Category')
    approval_ids = fields.Many2many('approval.request', string='Approvals ID',
                                    domain="[('vehi_divr_assigned_status', '=', 'un_assigned'), "
                                           "('request_status', '=', 'approved')]")
    model_id = fields.Many2one('fleet.vehicle.model', 'Allocated Vehicle',
                               tracking=True, help='Model of the vehicle',
                               domain="[('vehicle_type', '=', vehicle_category)]")
    vechicle_list = fields.Many2one('fleet.vehicle', string="Vechicles",
                                    domain="[('state_id', '=', 'Ready to Trip'),"
                                           "('vehicle_state', '=', 'un_reserved'),"
                                           "('model_id', '=', model_id),"
                                           "('vehicle_category', '=', vehicle_category)]")
    vehicle_driver = fields.Many2one('hr.employee', string='Driver',
                                     domain="[('emp_diver', '=', True),('driver_state', '=', 'un_reserved')]")

    def fleet_multiple_assign_vehicle(self):
        approval = self.env['approval.request'].search()
        for i in self.approval_ids:
            i.write({
                'model_id': self.model_id.id,
                'vechicle_list': self.vechicle_list.id,
                'vehicle_category': self.vehicle_category,
                'vehicle_driver': self.vehicle_driver.id,
            })
        approval.open_employee_trip_form()
