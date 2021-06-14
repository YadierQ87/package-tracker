# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, http, _
from odoo.http import request


class EnvoyPortal(http.Controller):

    @http.route([
        '/envoy-portal',
    ], type='http', auth="user", website=True)
    def index_portal(self, blog=None, tag=None, page=1, **opt):
        Reservation = request.env['cmp.reservation.container']
        reservations = Reservation.search([])
        return request.render("esp_componedor_paquetes.esp_cmp_layout_envoy_portal", {'reservations': reservations})
