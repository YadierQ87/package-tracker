# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"
    shipper_initials = fields.Char(string='Siglas Proveedor', size=8)
    transport_type = fields.Selection([("Aereo", "Aereo"),
                                       ("Maritimo", "Maritimo"),
                                       ("Terrestre", "Terrestre")],
                                      string="Tipo Transporte")
    ci = fields.Char("Carnet de Identidad", size=11)
    passport = fields.Char("Pasaporte", size=14)
    full_address = fields.Text(string='Direccion', compute="_compute_address", )
    second_name = fields.Char("Segundo Nombre")
    first_lastname = fields.Char("Primer Apellido")
    second_lastname = fields.Char("Segundo Apellido")
    nacionality = fields.Char("Nacionalidad")
    date_of_birth = fields.Date("Fecha de Nacimiento")
    num_house = fields.Char("Numero de la Casa")

    def _compute_address(self):
        for c in self:
            street = c.street + ', ' if c.street else ''
            street2 = c.street2 + ', ' if c.street2 else ''
            city = c.city + ', ' if c.city else ''
            state = c.state_id.name + ', ' if c.state_id.name else ''
            country = c.country_id.name + ', ' if c.country_id.name else ''
            czip = 'C.P ' + c.zip if c.zip else ''
            c.full_address = street + street2 + city + state + country + czip


# COMPANY
class ResCompany(models.Model):
    _inherit = "res.company"

    # COmercio Exterior
    pediment_key = fields.Char("Clave de Pedimento", default="A1")
    operation_type = fields.Char("Tipo de Operacion", default="2")
    origin_certified = fields.Char("Certificado de Origen", default="1")
    incoterm = fields.Char("Incoterm", default="CFR")
    subdivision = fields.Char("Subdivision", default="Subdivision")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    packages_detail = fields.Html()
