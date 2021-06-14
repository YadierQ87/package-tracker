# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools


#cmp.package.items agregarle los campos de provincia y municipio
class PackageItems(models.Model):
    _inherit = "cmp.package.items"

    province = fields.Char(related='destination.state_id.name',default='not set',store=True)
    city = fields.Char(related='destination.city',default='not set',store=True)
    sorting_rule = fields.Char(related='envoy_id.sorting_rule_id.name',default='not set',store=True)
