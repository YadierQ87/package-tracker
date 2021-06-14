# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

class EspAduanaEnvoyChecking(models.TransientModel):
    _name = 'aduana.envoy.checking'
    _description = 'Checking de Envio de Paquetes en la Aduana'

    name = fields.Char()#TODO sequence
    envoy_id = fields.Many2one("cmp.envoy")
    state = fields.Selection([("new", "new"),("open", "open"),("confirm","confirm"),("failed","failed")],default='new')
    list_package = fields.Many2many("cmp.package.items",compute="_compute_envoy_total_list",store=False)

    @api.depends('envoy_id')
    def _compute_envoy_total_list(self):
        self.list_package = self.env['cmp.package.items'].search(
            [('envoy_id', '=', self.envoy_id.id)])

    #TODO chequear para el envio todos sus paquetes
    def do_confirm(self):
        self.write({'state': "confirm"})

class EspAduanaPackageChecking(models.TransientModel):
    _name = 'aduana.package.checking'
    _description = 'Checking de paquetes o bultos en la Aduana'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(store=True,readonly=True,default='New')
    kanban_state = fields.Selection([ ('normal', 'Nuevo'), ('done', 'Confirmado'), ('blocked', 'Error')],
                                    string='Chequeo:',   copy=False, default='normal', required=True)
    state = fields.Selection([("new", "new"),
                              ("open", "open"),
                              ("confirm","confirm"),
                              ("failed","failed")],default='new',track_visibility="always")
    stage = fields.Selection([("Tienda", "Tienda"),
                              ("Aduana MEX", "Aduana MEX"),
                              ("Aduana CUB","Aduana CUB"),
                              ("Correo","Correo"),
                              ('dispatch','Despacho')],
                             default='Tienda',track_visibility="always")
    color = fields.Integer(string='Color Index')
    package_id = fields.Many2one("cmp.package.items",
                                 store=True,
                                 string="Seleccione Paquete para revision",
                                 domain="[('customs_state', '=','uncheck')]",
                                 required=True,
                                 )
    barcode_to_check = fields.Char("Codigo de Barras para chequear")
    count_check = fields.Integer(compute="_checking_barcode_items",
                                 string="Cantidad de Items Chequeados",
                                 default=0,store=True)
    list_items = fields.Many2many("cmp.sale.items", store=True)#reverse = 'package_id'
    error_html = fields.Html("Detalles del Error")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.aduana.packaging') or 'New'
        return super(EspAduanaPackageChecking, self).create(vals)

    @api.onchange('package_id')
    def _deafult_items_total_list(self):
        if self.package_id:
            self.list_items = self.package_id.sale_item_ids

    #se calcula la cantidad de articulos scaneados y se actualiza el checking
    @api.depends('barcode_to_check')
    def _checking_barcode_items(self):
        if self.count_check is False:
            self.count_check = 0
        if self.barcode_to_check != "":
            for i, item in enumerate(self.list_items):
                if item.barcode == self.barcode_to_check:
                    item.quantity_check += 1
                    if item.quantity_check == item.quantity:
                        item.customs_state = "ok"
                    if item.quantity_check > item.quantity:
                        item.customs_state = "failed"
            self.barcode_to_check = ""
            self.count_check += 1

    def _check_list_items(self):
        if self.package_id and self.list_items:
            self.package_id.customs_state = "ok"
            self.package_id.state = "confirm"
            self.kanban_state = "done"
            for i, item in enumerate(self.list_items):
                if item.customs_state != "ok":
                    self.package_id.customs_state = "failed"
                    self.state = "failed"
                    self.kanban_state = "blocked"

    def write(self, vals):
        if self.package_id == False or self.list_items == False:
            raise ValidationError('Debe seleccionar al menos un paquete para validar!')
        return super(EspAduanaPackageChecking, self).write(vals)

    #botones
    def do_uncheck_all(self):
        if self.package_id and self.list_items:
            for i, item in enumerate(self.list_items):
                item.customs_state = "uncheck"
                item.quantity_check = 0

    def do_pass_this_stage(self):
        if self.package_id and self.list_items:
            self._check_list_items()
            if self.kanban_state == "blocked":
                raise ValidationError('Faltan articulos por confirmar o tienen errores')
            if self.kanban_state == "done":
                self.do_uncheck_all()
                self.kanban_state = "normal"
                if self.stage == "Tienda":
                    return self.write({'stage': 'Aduana MEX'})
                if self.stage == "Aduana MEX":
                    return self.write({'stage': 'Aduana CUB'})
                if self.stage == "Aduana CUB":
                    return self.write({'stage': 'Correo'})
                if self.stage == "Correo":
                    return self.write({'stage': 'dispatch'})
        else:
            raise ValidationError('Debe seleccionar al menos un paquete para validar!')





