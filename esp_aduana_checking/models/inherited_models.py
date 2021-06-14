# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools

class Envoy(models.Model):
    _inherit = "cmp.envoy"
    customs_state = fields.Selection([("uncheck", "uncheck"),
                                      ("ok", "ok"),("failed", "failed")], default="uncheck")

class PackageItems(models.Model):
    _inherit = "cmp.package.items"

    customs_state = fields.Selection([("uncheck", "uncheck"),
                                      ("ok", "ok"), ("failed", "failed")], default="uncheck")
    #original_state = fields.Char(compute='_get_last_modified_status')
    aduana_checking_ids = fields.One2many('aduana.package.checking','package_id')


# Sal items
class CmpSaleItems(models.Model):
    _inherit = "cmp.sale.items"
    #for customs
    customs_state = fields.Selection([("uncheck", "uncheck"),
                                      ("ok", "ok"),("failed", "failed")],
                                     default="uncheck",string="Estado")
    stage = fields.Selection([("tienda", "tienda"),
                              ("aduana_init", "aduana_init"),
                              ("aduana_end", "aduana_end"),
                              ("mailing", "mailing")], default='tienda')
    quantity_check = fields.Integer(default=0,string="Cantd Chequeada",store=True)
    barcode = fields.Char(related='item_id.barcode')

    def do_check(self):
        """ Makes event invitation as Tentative. """
        self.write({'customs_state': 'ok'})
        self.write({'quantity_check': self.quantity})

    def do_failed(self):
        """ Makes event invitation as Tentative. """
        self.write({'quantity_check': 0})
        return self.write({'customs_state': 'failed'})


