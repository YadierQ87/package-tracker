# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime

from odoo import api, fields, models, _, tools
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

# clase que guarda los embarques
class ReservationContainer(models.Model):
    _name = "cmp.reservation.container"
    _description = "Reserva para contener los envios de paquetes"
    _order = "shipping_date"

    name = fields.Char(string='Nombre de Reserva-Carga', readonly=True, compute="_compute_name", default='EMB/')
    codigo = fields.Char(string='Codigo de Reserva-Carga', readonly=True,
                         required=True, copy=False, default='New Embarque-Carga')
    tipo_transporte = fields.Selection([("Aereo", "Aereo"),
                                        ("Maritimo", "Maritimo"),
                                        ("Terrestre", "Terrestre")],
                                       string="Tipo Transporte")
    shipping_date = fields.Date("Fecha Prevista Embarque (ETS)")
    real_shipping_date = fields.Date("Fecha Real Salida")
    real_arriving_date = fields.Date("Fecha Real Arribo")
    capacity_type = fields.Selection([("Volumen m3", "Volumen m3"),
                                      ("Peso Kg", "Peso Kg")], string="Tipo de Capacidad")
    freight = fields.Selection([("prepaid", "prepaid"),
                                ("collect", "collect"),
                                ("elsewhere", "elsewhere")], string="Puerto a pagar")
    shipping_capacity = fields.Float("Capacidad Embarque")
    shipper = fields.Many2one("res.partner",
                              "Proveedor Embarque")  # todos tienen un nomenclador siglas shipper_initials
    forwarder = fields.Many2one("res.partner", "Transitario")  # todos tienen un nomenclador siglas shipper_initials
    vessel = fields.Many2one("res.partner", "Nave")  # todos tienen un nomenclador siglas shipper_initials
    shipment_origin = fields.Many2one("res.partner", "Puerto Origen")
    shipment_destiny = fields.Many2one("res.partner", "Puerto Destino")
    transportation_tax = fields.Float("Impuesto transportacion")
    transportation_cost = fields.Float("Costo Reservacion")
    envoys_total_ids = fields.One2many("cmp.envoy.total", "container_id", string="Lista de envios")
    real_capacity = fields.Float(string="Espacio disponible", compute="_compute_capacity")
    active = fields.Boolean("Activo?", default=True)
    state = fields.Selection([("new", "new"), ("open", "open"), ("closed", "closed"), ("delivered", "delivered")])
    no_contenedor = fields.Char(string="No. Contenedor")  # se registra solo cuando el embarque pasa a state=delivered
    # state in closed no se permite agregar mas envios de bultos en ese embarque
    html_records = fields.Html(compute="_list_for_all_products", store=False)
    html_pack_short = fields.Html(compute="_list_for_all_products", store=False)
    trip_number = fields.Char(string="Numero de viaje")
    container_data = fields.Text(string="Detalles del contendor")
    #totales computados para los productos
    total_items = fields.Integer(compute="_list_for_all_products",string="Total Productos")
    total_cost = fields.Float(compute="_list_for_all_products",string="Costo Total")
    total_volume = fields.Float(compute="_list_for_all_products",string="Volumen Total")
    total_weight = fields.Float(compute="_list_for_all_products",string="Peso Total")
    total_bags = fields.Integer(compute="_list_for_all_products",string="Total Bultos")
    manifest_xml_name = fields.Char(readonly=True,
                         required=True, copy=False, default='New')
    hbl_bl_code = fields.Char("Guia aerea o BL hijo para el maritimo")
    currency_exchange = fields.Float("Tasa de Cambio USD")
    usd_total = fields.Float("Total USD")

    @api.constrains('shipping_date', 'real_shipping_date')
    def _check_dob_date(self):
        current_date = (datetime.today()).strftime("%d/%m/%YY")
        c_date = datetime.strptime(current_date, "%d/%m/%YY").date()
        for record in self:
            d_date = record.shipping_date
            if d_date and c_date >= d_date:
                raise UserError("La fecha prevista embarque no puede ser menor de Hoy!")

    @api.depends('shipper', 'shipment_destiny', 'shipping_date')
    def _compute_name(self):
        for item in self:
            if item.shipper.name and item.shipment_destiny.name and item.shipping_date:
                item.name = "EMB/" + item.shipper.name + "-" + item.shipment_destiny.name + "," + str(
                    item.shipping_date)
            else:
                item.name = "EMB/"

    @api.model
    def create(self, vals):
        if vals.get('codigo', 'New Embarque-Carga') == 'New Embarque-Carga':
            vals['codigo'] = self.env['ir.sequence'].next_by_code(
                'cmp.reservation.container') or 'New Embarque-Carga'
        if vals.get('manifest_xml_name', 'New') == 'New':
            vals['manifest_xml_name'] = 'Manifiesto' + str(self.env['ir.sequence'].next_by_code(
                'cmp.reservation.container')) + "20210803" + "PC"
        result = super(ReservationContainer, self).create(vals)
        return result

    def _compute_capacity(self):
        occupied = 0
        for envoy_total in self.envoys_total_ids:
            occupied += envoy_total.weight
        self.real_capacity = self.shipping_capacity - occupied

    # llamadas a sql para los reportes
    def _list_for_all_products(self):
        sql = """SELECT 
              cmp_sale_items.item_id, 
              product_template.description,
              SUM (cmp_sale_items.quantity) as total_items,
              product_template.weight, 
              product_template.volume,
              product_template.bags,
              cmp_product_brand.name as marca,
              cmp_product_model.name as modelo,
              product_template.list_price,
              cmp_fraccion_arancelaria.name as fracion,
              cmp_fraccion_arancelaria.material as material,
              product_template.name 
            FROM 
              public.cmp_sale_items 
              left JOIN product_template ON cmp_sale_items.item_id = product_template.id 
              left JOIN cmp_fraccion_arancelaria ON product_template.fraction_id = cmp_fraccion_arancelaria.id 
              left JOIN cmp_product_brand ON product_template.brand_id = cmp_product_brand.id 
              left JOIN cmp_product_model ON product_template.modelo_id = cmp_product_model.id 
              left JOIN cmp_package_items ON cmp_sale_items.package_id = cmp_package_items.id 
              left JOIN cmp_envoy ON cmp_package_items.envoy_id = cmp_envoy.id 
              left JOIN cmp_envoy_total ON cmp_envoy.total_envoy_id = cmp_envoy_total.id 
              left JOIN cmp_reservation_container ON cmp_envoy_total.container_id = cmp_reservation_container.id
              WHERE cmp_reservation_container.id = %s
              GROUP BY cmp_sale_items.item_id, 
                    product_template.description ,product_template.weight,
                    product_template.bags,
                    cmp_product_brand.name,  cmp_product_model.name,
                    product_template.list_price, 
		            cmp_fraccion_arancelaria.name,cmp_fraccion_arancelaria.material,
                    product_template.volume , product_template.name""" % self.id
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        total_items = total_bags = 0
        total_volume = total_weight = total_cost = 0.0
        html_products = html_pack_short = ""
        for item in result:
            coste = 0
            fracion = material = modelo = marca = ""
            if item['total_items']:
                total_items += item['total_items']
            if item['bags']:
                total_bags += item['bags']
            if item['volume']:
                total_volume += item['volume']
            if item['list_price']:
                coste = item['total_items'] * item['list_price']
                total_cost += coste
            if item['weight']:
                total_weight += item['weight']
            if item['fracion']:
                fracion = item['fracion']
            if item['material']:
                material = item['material']
            if item['modelo']:
                modelo = item['modelo']
            if item['marca']:
                marca = item['marca']
            html_pack_short += """<tr>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                </tr>""" % (item['item_id'], item['name'],fracion,marca,
                            item['total_items'],item['list_price'],coste)
            html_products += """<tr>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >No Serie</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                </tr>""" % (item['item_id'], item['name'],fracion,material,marca,modelo,
                            item['total_items'],item['list_price'],coste,
                            item['volume'],item['weight'],item['bags'])
        #_logger.info(" Mensaje listado %s", html_products)
        self.html_records = html_products
        self.html_pack_short = html_pack_short
        self.total_items = total_items
        self.total_cost = total_cost
        self.total_volume = total_volume
        self.total_weight = total_weight
        self.total_bags = total_bags
