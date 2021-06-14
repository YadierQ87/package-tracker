# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
import math
from datetime import datetime
from io import BytesIO

import qrcode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
# import tools

class PackageItems(models.Model):
    _name = "cmp.package.items"
    _description = "Paquete de articulos de un envio"
    _order = 'hbl_header'

    # name = fields.Char(compute='_compute_package', string='HBL', readonly=True, copy=False, store=True)
    name = fields.Char(string='No Serie', readonly=True,
                       required=True, copy=False, default='New Package')
    envoy_id = fields.Many2one('cmp.envoy', string="No. Envio", ondelete='cascade')
    sender = fields.Many2one('res.partner', related="envoy_id.sender",
                             string='Remitente:', required=False, translate=True)
    destination = fields.Many2one('res.partner', related="envoy_id.destination",
                                  string='Destinatario:', required=False, translate=True)
    notify = fields.Many2one('res.partner', related="envoy_id.notify",
                             string='Notificar a:', required=False, translate=True)
    sorting_rule_id = fields.Many2one('cmp.sorter.rule', related="envoy_id.sorting_rule_id")
    sale_item_ids = fields.One2many('cmp.sale.items', 'package_id', string='Listado de Articulos', ondelete='cascade')
    price_unit = fields.Float(related="sorting_rule_id.price_unit", string='Costo de la Regla', default=0.0)
    quantity = fields.Integer(compute='_compute_package',
                              string='Cantidad', translate=True, default=0)  # Cantidad de articulos x paquete
    weight = fields.Float('Peso kg', compute='_compute_package', default=0.0)
    volume = fields.Float('Volumen m3', compute='_compute_package', default=0.0)
    price_neto = fields.Float(compute='_compute_package', string='Costo Neto del paquete', default=0.0)
    description = fields.Text(compute='_compute_package', readonly=True)
    bags = fields.Integer(compute='_compute_package', readonly=True)
    container_id = fields.Many2one("cmp.reservation.container", related="envoy_id.container_id",
                                   string="Reserva de Embarque")
    hbl_header = fields.Char(compute='_gen_hbl', readonly=True, search='_search_hbl', store=True)
    barcode = fields.Char(compute='_compute_barcode', readonly=True, search='_search_hbl', store=True)
    seed = fields.Char(default='87654321', readonly=True)
    qr_code = fields.Binary(compute="generate_qrcode", string="QR Code", attachment=True, store=True)
    item_types = fields.Char(compute="get_types", string="Tipos de articulo")

    @api.model
    @api.depends('sale_item_ids')
    def get_types(self):
        for p in self:
            types = []
            _logger.info('computint types')
            for s in p.sale_item_ids:
                if not s.item_id.category_id.simple_id:
                    continue
                try:
                    types.index(s.item_id.category_id.simple_id.name)
                    _logger.info('adding type')
                except ValueError:
                    types.append(s.item_id.category_id.simple_id.name)
                    _logger.info('type not found')
            p.item_types = ""
            for t in types:
                p.item_types += t + "\n"

    @api.model
    @api.depends('sale_item_ids')
    def generate_qrcode(self):
        for p in self:
            qr_data = ""
            for item in p.sale_item_ids:
                qr_data += item.item_id.name + " X" + str(item.quantity) + "\n"

            p.qr_code = gen_qr(qr_data)

    @api.model
    def _search_hbl(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('hbl_header', operator, value)]

    @api.model
    def create(self, vals):
        if vals.get('name', 'New Package') == 'New Package':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cmp.package.items') or 'New Package'
        result = super(PackageItems, self).create(vals)
        return result

    @api.model
    @api.depends('name')
    def _compute_barcode(self):
        for p in self:
            cons = p.name
            v = 0
            for i, s in enumerate(p.seed):
                # _logger.info('V is %d', v)
                v += int(s)  # * int(cons[i])
            v = v % 11
            if v == 1:
                v = 0
            elif v == 0:
                v = 5
            else:
                v = 11
            p.barcode = 'CP' + cons + str(v) + 'EP'

    @api.model
    @api.depends('sale_item_ids')
    def _gen_hbl(self):
        company = self.env.company.partner_id.shipper_initials
        for p in self:
            o = p.container_id.shipment_origin.shipper_initials
            d = p.container_id.shipment_destiny.shipper_initials
            n = p.name
            p.hbl_header = (company if company else 'Nc') + (o if o else 'No') + (d if d else 'Nd') + \
                           (n if n else 'Nn')

    @api.model
    @api.depends('sale_item_ids')
    def _compute_package(self):
        for package in self:
            weight = volume = quantity = bags = 0
            description = ""
            for sale_item in package.sale_item_ids:
                if sale_item.weight:
                    weight += sale_item.weight * sale_item.quantity
                if sale_item.volume:
                    volume += sale_item.volume * sale_item.quantity
                quantity += sale_item.quantity
                bags += sale_item.item_id.bags * sale_item.quantity
                description += str(sale_item.name) + "\n"
            package.volume = volume
            package.weight = weight
            package.quantity = quantity
            package.price_neto = package.price_unit
            package.description = description
            # package.name = package.hbl_header
            if package.sorting_rule_id.one_bag:
                package.bags = 1
            else:
                package.bags = bags
            if package.volume > 0:
                package.price_neto = package.price_unit * package.volume

    @api.model
    @api.depends('sale_item_ids')
    def get_weight(self):
        weight = 0
        for sale_item in self.sale_item_ids:
            weight += sale_item.weight * sale_item.quantity
        # _logger.info("package weight should be %f", weight)
        return weight

    def find_item(self, sale_item):
        count = 0
        # _logger.info('list of items is %f items long', len(self.sale_item_ids))
        for sale in self.sale_item_ids:
            # _logger.info('existing decription: %f \t\t new description %f', sale.description, sale_item.description)
            if sale.item_id == sale_item.item_id:
                return count
            count += 1
        return -1

    def add_item(self, sale_item):
        index = self.find_item(sale_item)
        if index != -1:
            self.sale_item_ids[index].quantity += 1
        else:
            sale = self.env['cmp.sale.items']
            new = sale.create({'quantity': 1})
            new.description = sale_item.description
            new.item_id = sale_item.item_id.id
            new.weight = sale_item.weight
            self.sale_item_ids |= new


class Envoy(models.Model):
    _name = "cmp.envoy"
    _description = "Tipo envio"

    name = fields.Char(string='Codigo del envio', readonly=True, required=True, copy=False, default='HBL')  # HBL
    total_envoy_id = fields.Many2one('cmp.envoy.total', string="No. Envio", ondelete='cascade')
    active = fields.Boolean("Activo?", default=True)
    sender = fields.Many2one('res.partner', related="total_envoy_id.sender",
                             string='Remitente:', required=True, translate=True)
    state = fields.Selection([("new", "new"), ("in-way", "in-way"),
                              ("on-time", "on-time"), ("delayed", "delayed"),
                              ("arrived", "arrived"), ("delivered", "delivered")])
    destination = fields.Many2one('res.partner', string='Destinatario:', required=False, translate=True)
    notify = fields.Many2one('res.partner', string='Notificar a:', required=False, translate=True)
    sorting_rule_id = fields.Many2one('cmp.sorter.rule', string='Regla de Envio:', required=True,
                                      translate=True)  # categoria del envio
    packages_ids = fields.One2many('cmp.package.items', 'envoy_id', string='Lista de Paquetes', readonly=False,
                                   translate=True, ondelete='cascade')
    # atributos del total de paquetes
    weight = fields.Float('Peso Total kg', compute='_compute_total_package')
    volume = fields.Float('Volumen Total m3', compute='_compute_total_package')
    delivery_price = fields.Float('Costo del Envio', compute='_compute_total_package')
    total_items = fields.Integer('Total Articulos', compute='_compute_total_package')
    container_id = fields.Many2one("cmp.reservation.container", related="total_envoy_id.container_id",
                                   string="Reserva de Embarque")
    package_quantity = fields.Integer(compute='_compute_total_package')  # para conocer el total de paquetes
    item_types = fields.Char(compute="get_types", string="Tipos de articulo")
    qr_code = fields.Binary(compute="generate_qrcode", string="QR Code", attachment=True, store=True)

    @api.model
    @api.depends('packages_ids')
    def get_types(self):
        for e in self:
            types = []
            for p in e.packages_ids:
                types.append(p.item_types)
            rtypes = []
            for word in types:
                if word not in rtypes:
                    rtypes.append(word)
            e.item_types = ""
            for t in rtypes:
                e.item_types = t + "\n"

    @api.model
    def create(self, vals):
        if vals.get('name', 'HBL') == 'HBL':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cmp.envoy') or 'HBL'
        result = super(Envoy, self).create(vals)
        return result

    @api.model
    # @api.depends('packages_ids')
    def _compute_total_package(self):
        for envoy in self:
            weight = volume = price = items = package_quantity = 0
            for package in envoy.packages_ids:
                if package.weight:
                    weight += package.weight
                if package.volume:
                    volume += package.volume
                if package.price_neto:
                    price += package.price_neto
                if package.quantity:
                    items += package.quantity
                package_quantity += 1  # added package_quantity
            envoy.weight = weight
            envoy.volume = volume
            envoy.delivery_price = price
            envoy.total_items = items
            envoy.package_quantity = package_quantity

    @api.model
    @api.depends('packages_ids')
    def generate_qrcode(self):
        for e in self:
            qr_data = ""
            for p in e.packages_ids:
                qr_data += p.hbl_header + "\n"

            e.qr_code = gen_qr(qr_data)

    def process_bundle(self, bundle) -> bool:
        if self.packages_ids:
            for package in self.packages_ids:
                if package.quantity == 0:
                    self.write({"packages_ids": [(2, package.id)]})  # borrar todos los envios asociados
        _logger.info('there are currently %d\n%s', len(self.packages_ids), self.packages_ids)
        if len(self.packages_ids) < self.sorting_rule_id.max_units:
            new: PackageItems = self.env['cmp.package.items'].create({'envoy_id': self.id})
            _logger.info("Opening Combo: %s", bundle.item_id.name)
            for b in bundle.item_id.bundle_items:
                _logger.info("The line %s", b.item_id.name)
                for i in range(math.ceil(b.quantity)):
                    _logger.info("This is the %d bag", self.count_current(b.item_id))
                    if self.in_package_count(new, b.item_id) >= b.item_id.category_id.max_count:
                        message = "El combo \"%s\" fallo a causa del articulo \"%s\"\n" \
                                  % (bundle.item_id.name, b.item_id.name)
                        message += " excedido numero permitido de \"%s\"" % b.item_id.category_id.name
                        raise ValidationError(message)
                    if self.count_current(b.item_id) < b.item_id.category_id.max_count:
                        new.add_item(b)
                    else:
                        _logger.info("Can't fit the combo in here")
                        self.write({"packages_ids": [(2, new.id)]})
                        return False
            # self.packages_ids |= new
            return True
        return False

    def proccess_list_item(self, entry_list):
        full_list = entry_list
        discarded = []
        # _logger.info('tamaño de la lista %s', len(full_list))
        count = 0
        while len(full_list) > 0:
            if len(self.packages_ids) >= self.sorting_rule_id.max_units:
                discarded.extend(full_list)
                # self.crear_descartados(discarded)

                if self.packages_ids:
                    for package in self.packages_ids:
                        if package.quantity == 0:
                            self.write({"packages_ids": [(2, package.id)]})  # borrar todos los envios asociados
                return discarded

            count += 1
            # _logger.info('hay que crear')
            new = self.env['cmp.package.items'].create({'envoy_id': self.id})
            self.packages_ids |= new
            for package in self.packages_ids:
                to_remove = []
                for i in full_list:
                    if i.item_id.is_bundle:
                        if not self.process_bundle(i):
                            discarded.append(i)
                        to_remove.append(i)
                    else:
                        if i.weight > self.sorting_rule_id.max_unit_weight:
                            discarded.append(i)
                            to_remove.append(i)
                            continue
                        _logger.info('package weight %f - %f = %f',
                                     self.sorting_rule_id.max_unit_weight, package.get_weight(),
                                     self.sorting_rule_id.max_unit_weight - package.get_weight())
                        if i.weight <= self.sorting_rule_id.max_unit_weight - package.get_weight():
                            if self.count_current(i.item_id) < i.item_id.category_id.max_count:
                                if self.sorting_rule_id.max_points == 0 \
                                        or i.item_id.price < self.sorting_rule_id.max_points - package.price_unit:
                                    # _logger.info('addingItemToPackage')
                                    package.add_item(i)
                                    to_remove.append(i)
                                    # i.quantity -= 1
                                    # continue
                                else:
                                    # _logger.info('descartado por espacio')
                                    discarded.append(i)
                                    to_remove.append(i)
                            else:
                                discarded.append(i)
                                to_remove.append(i)
                                # _logger.info('descartado por limite')
                for i in to_remove:
                    full_list.remove(i)

        if self.packages_ids:
            for package in self.packages_ids:
                if package.quantity == 0:
                    self.write({"packages_ids": [(2, package.id)]})  # borrar todos los envios asociados

        return discarded

    def crear_descartados(self, discarded):
        new = self.env['cmp.package.items'].create({'name': 'descartados'})
        self.packages_ids |= new

        for item in discarded:
            self.packages_ids[-1].add_item(item)

    @staticmethod
    def in_package_count(package: PackageItems, item):
        count = 0
        for sale_item in package.sale_item_ids:
            if sale_item.category_id == item.category_id:
                if sale_item.category_id.um == 'kg':
                    _logger.info('category is kg')
                    count += sale_item.quantity * sale_item.item_id.weight
                else:
                    count += sale_item.quantity
        return count

    def count_current(self, item):
        count = 0
        for package in self.packages_ids:
            # count += (
            #     len(list(filter(lambda x: x.item_id.category_id == item.item_id.category_id, package.sale_item_ids))))
            for sale_item in package.sale_item_ids:
                if sale_item.item_id.is_bundle:
                    for b in sale_item.item_id.bundle_items:
                        if b.item_id.category_id == item.category_id:
                            if b.category_id.um == 'kg':
                                count += b.quantity * b.item_id.weight
                            elif b.category_id.um == 'lt':
                                count += b.quantity * b.item_id.volume
                            else:
                                count += b.quantity

                elif sale_item.category_id == item.category_id:
                    if sale_item.category_id.um == 'kg':
                        _logger.info('category is kg')
                        count += sale_item.quantity * sale_item.item_id.weight
                    else:
                        count += sale_item.quantity
        return count


class TotalEnvoy(models.Model):
    _name = "cmp.envoy.total"
    _description = "Venta de varios envios a un Cliente"

    name = fields.Char(string='Codigo de lista de envio', readonly=True,
                       required=True, copy=False, default='New Total Envoy')  # HBL
    active = fields.Boolean("Activo?", default=True)
    sender = fields.Many2one('res.partner', string='Remitente:', required=True, translate=True)
    sorting_rule_id = fields.Many2one('cmp.sorter.rule', string='Regla de Envio:', required=True, )
    entry_sale_items = fields.One2many('cmp.sale.items', 'total_envoy_id', string='Lista de Articulos')
    envoy_ids = fields.One2many('cmp.envoy', 'total_envoy_id', string='Lista de Envios', translate=True,
                                ondelete='cascade')
    state = fields.Selection([
        ("borrador", "borrador"),
        ("creado", "creado"),
        ("cancelado", "cancelado"),
        ("facturado", "facturado"),
        ("cobrado", "cobrado"), ("despachado", "despachado")], default="creado")
    weight = fields.Float(compute="_compute_total", string="Peso neto", default=0)
    cost = fields.Float(compute="_compute_total", string="Costo Total", default=0)
    envoy = fields.Float(compute="_compute_total", string="Total de Envios", default=0)
    packages = fields.Float(compute="_compute_total", string="Total de Paquetes", default=0)
    sale_items = fields.Float(compute="_compute_total", string="Total de Articulos", default=0)
    container_id = fields.Many2one("cmp.reservation.container", string="Reserva de Embarque")
    container_real_capacity = fields.Float(related="container_id.real_capacity")
    no_sale_order_id = fields.Many2one("sale.order")
    sale_order_name = fields.Char(related="no_sale_order_id.name")

    # print reporte proforma
    def action_quotation_send(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'esp_componedor_paquetes.new_package_report_saleorder_document',
            'model': 'cmp.envoy.total',
            'report_type': "qweb-pdf"
        }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New Total Envoy') == 'New Total Envoy':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cmp.envoy.total') or 'New Total Envoy'
        result = super(TotalEnvoy, self).create(vals)
        return result

    @api.model
    def _compute_total(self):
        weight = delivery_price = packages_amount = sale_item_amount = 0
        for envoy in self.envoy_ids:
            weight += envoy.weight
            delivery_price += envoy.delivery_price
            packages_amount += len(envoy.packages_ids)
            sale_item_amount += envoy.total_items
        self.weight = weight
        self.cost = delivery_price
        self.packages = packages_amount
        self.sale_items = sale_item_amount
        self.envoy = len(self.envoy_ids)

    def total_process(self):
        if self.envoy_ids:
            for envoy in self.envoy_ids:
                self.write({"envoy_ids": [(2, envoy.id)]})  # borrar todos los envios asociados
        the_list = self.disaggregated()
        count = 1
        while len(the_list) > 0:
            envoy = self.env['cmp.envoy']
            new = envoy.sudo().create({'sorting_rule_id': self.sorting_rule_id.id})
            the_list = new.proccess_list_item(the_list)
            self.envoy_ids |= new
            count += 1
        self.state = "creado"
        package_items = self.env['cmp.package.items']
        envs = self.env['cmp.envoy']
        self.env.add_to_compute(package_items._fields['qr_code'], package_items.search([]))
        self.env.add_to_compute(envs._fields['qr_code'], envs.search([]))

    def disaggregated(self):
        full_list = []
        for sale in self.entry_sale_items:
            _logger.info(sale)
            for i in range(int(sale.quantity)):
                full_list.append(sale)
        full_list.sort(key=lambda x: x.weight, reverse=True)
        full_list.sort(key=lambda x: x.item_id.is_bundle, reverse=True)
        return full_list

    # action button que crea una Facutra sale.order de varios productos para ese envio
    def create_invoce_envoy(self):
        if self.state != "facturado":
            Venta = self.env["sale.order"]
            today = datetime.today()
            new_sale_order = Venta.create({'partner_id': self.sender.id,
                                           'partner_invoice_id': self.sender.id,
                                           'partner_shipping_id': self.sender.id,
                                           'date_order': today})
            LineasVentas = self.env["sale.order.line"]
            ProductoStandard = self.env["product.template"].search([('name', 'ilike', 'Envio Paquete')])
            if ProductoStandard:
                product_id = ProductoStandard.id
                ProductoProd = self.env["product.product"].search([('product_tmpl_id', '=', product_id)])
            else:
                raise ValidationError("Se debe configurar el Producto Envio Paquete")
            if self.envoy_ids:  # cantidad de envios creados
                for envoy in self.envoy_ids:
                    LineasVentas.create({
                        'order_id': new_sale_order.id,
                        'name': "Envio: " + envoy.name,
                        'product_id': ProductoProd.id,
                        'product_uom_qty': 1,
                        'price_unit': envoy.delivery_price
                    })
            message = "Venta: %s registrada con exito" % new_sale_order
            self.msg_display_notification("Operacion Exitosa", message)
            self.state = "facturado"
            self.no_sale_order_id = new_sale_order.id

    def msg_display_notification(self, title, msg):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(msg),
                'sticky': True,
            }
        }
        return notification

    def go_to_sales_order(self):
        pass

    # action button que genera la asignacion de embarques
    # reservados disponibles por el peso y el volumen adecuado
    def assign_reservation_envoy(self):
        pass


def gen_qr(qr_data):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_image = base64.b64encode(temp.getvalue())
    return qr_image
