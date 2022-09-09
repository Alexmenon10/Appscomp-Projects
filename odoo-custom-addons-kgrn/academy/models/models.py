# -*- coding: utf-8 -*-

from odoo import models, fields, api


class academy(models.Model):
    _name = 'academy.academy'
    _description = 'academy.academy'

    name = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one("res.country")
    description = fields.Text()
