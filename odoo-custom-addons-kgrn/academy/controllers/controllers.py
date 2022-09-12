# -*- coding: utf-8 -*-
import requests
from odoo import http
from odoo.http import request


class SaleOrder(http.Controller):

    @http.route('/sale', auth='public')
    def index(self, **kw):
        return "Sale Order"

    @http.route('/sale/saleorder', auth='public', website='True')
    def list(self, **kw):
        return request.render('academy.sale_order', {
            'root': '/sale',
            'objects': request.env['sale.order'].search([]),
            'emp_list': request.env['hr.employee'].search([]),
        })

    @http.route('/employee', auth='public', website='True')
    def employee(self, **kw):
        return request.render('academy.emplyoee_list', {
            'emp_list': request.env['hr.employee'].search([]),
        })

    @http.route('/sale/saleorder/<model("sale.order"):obj>', auth='public', website='True')
    def object(self, obj):
        return request.render('academy.sale_id', {
            'object': obj
        })

    @http.route('/emp/<model("hr.employee"):employee>', auth='public', website='True')
    def object(self, employee):
        return request.render('academy.employee_profile', {
            'select_emp': employee
        })

    @http.route('/employee/employee_create', type='http', auth='public', website='True')
    def employee_create(self, **kw):
        res = request.render('academy.employee_card', {
            'country': request.env['res.country'].sudo().search([]),
            'state': request.env['res.country.state'].sudo().search([])
        })
        return res

    @http.route('/create/new_employee', type='http', auth='public', website='True')
    def employee_create_success(self, **kw):
        request.env['hr.employee'].sudo().create(kw)
        return request.redirect('/employee')

    # Method Used for RPC cALL
    @http.route('/add/value', auth='public', website=True)
    def add_value_json(self, **kw):
        return request.render('academy.add_value', {})

    # tHIS METHOD CALLED FROM JS AND VALUE RETURN TO JS
    @http.route('/add/value/sum', type="json", auth='public')
    def add_value_sum_json(self, **kw):
        num1 = kw.get('num1')
        num2 = kw.get('num2')
        sum = num1 + num2
        return {'sum': sum}

    @http.route('/partner/partner_list', auth='public', website='True')
    def partner_list(self, **kw):
        return request.render('academy.partner_list', {
            'partner_list': request.env['res.partner'].search([]),
        })

    # Method Used for API cALL
    @http.route('/weather/api', auth='public', type='http', website=True, csrf=False)
    def weather_values(self, **kw):
        country = kw.get('weather')
        url = "http://api.weatherapi.com/v1/current.json?key=a95e9f0a21894ee4ac093904220608&q=%s&aqi=no" % country
        payload = {
        }
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            value = response.json()
            res_patner = {
                'name': value.get('location')['name'],
            }
            patner = request.env['res.partner'].sudo().create(res_patner)
        return request.render('academy.weather_api', {})
