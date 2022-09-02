# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Management Extended",
    "version": "15.0.0.0.1",
    "author": "Appscomp",
    "category": "Hotel Management",
    "website": "",
    "depends": ["hotel"],
    "license": "LGPL-3",
    "summary": "Hotel Management to Manage Reservation Details",
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "data/hotel_reservation_sequence.xml",
        "data/hotel_scheduler.xml",
        "data/email_template_view.xml",
        "report/checkin_report_template.xml",
        "report/checkout_report_template.xml",
        "report/room_max_report_template.xml",
        "report/hotel_reservation_report_template.xml",
        "report/report_view.xml",
        # "wizard/hotel_reservation_wizard.xml",
        "views/hotel_reservation_view.xml",
        "views/hotel_folio_state.xml",
        "views/guest_reservations.xml",
        # "views/assets.xml",
    ],
    'assets': {
        'web.assets_qweb': [
            'hotel_extended/static/src/xml/hotel_room_summary.xml',
        ],
        'web.assets_backend': [
            'hotel_extended/static/src/css/room_summary.css',
            'hotel_extended/static/src/js/hotel_room_summary.js',
        ],
    },
    "external_dependencies": {"python": ["python-dateutil"]},
    "images": ["static/description/Hotel.png"],
    "application": True,
}
