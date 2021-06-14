# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SimpleCategory(models.Model):
    _name = "cmp.category.item.simple"
    _description = "Categoria generica para articulo"

    name = fields.Char(string='Tipo Generico', required=True, translate=True)


class CategoryItem(models.Model):
    _name = "cmp.category.item"
    _description = "Tipo de Categoria de Articulos aduana"

    name = fields.Char(string='Tipo Articulo', required=True, translate=True)
    # um = fields.Char(string='UM', required=True, translate=True)
    um = fields.Selection([
        ('one', 'Unidad'),
        ('kg', 'Kg'),
        ('m3', "Metros Cubicos"),
        ('lt', 'Litros')], string='UM', default="one", required=True, translate=True)
    description = fields.Text(string='Descripcion', translate=True)
    # item_type = fields.Selection([
    #     ('Miscelaneas', 'Miscelaneas'),
    #     ('Medicinas', 'Medicinas'),
    #     ('Electrodomesticos', 'Electrodomesticos')
    # ], string='Tipo de Articulo', translate=True)
    simple_id = fields.Many2one("cmp.category.item.simple", string='Tipo Generico', translate=True)
    max_count = fields.Float(string='Cantd Max Permitida', required=True, translate=True)
    price = fields.Float(string='Precio Articulo', required=True, translate=True)


class MarcaProducto(models.Model):
    _name = "cmp.product.brand"
    _description = "Marca para los productos"

    name = fields.Char()
    supplier = fields.Many2one("res.partner", "Fabricante o Proveedor")
    model_ids = fields.One2many("cmp.product.model", "brand_id")


class ModeloProducto(models.Model):
    _name = "cmp.product.model"
    _description = "Modelo para los productos"

    name = fields.Char()
    brand_id = fields.Many2one("cmp.product.brand")


class FraccionArancelaria(models.Model):
    _name = "cmp.fraccion.arancelaria"
    _description = "Fracciones arancelarias y codigos aduanales para los productos"

    name = fields.Char("Codigo de la Fraccion Arancelaria")
    material = fields.Char("Material Constituido")


class Product(models.Model):
    _inherit = "product.template"

    category_id = fields.Many2one('cmp.category.item', string='Categoria Articulo', translate=True)
    bags = fields.Integer(string='Bultos que lo componen', default=1)
    brand_id = fields.Many2one("cmp.product.brand")
    brand_name = fields.Char(related="brand_id.name")
    modelo_id = fields.Many2one("cmp.product.model", domain="[('brand_id', '=',brand_id)]")
    modelo_name = fields.Char(related="modelo_id.name")
    customs_price = fields.Float(string="Precio Aduana")
    fraction_id = fields.Many2one("cmp.fraccion.arancelaria", string="Fraccion Arancelaria")
    fraction_name = fields.Char(related="fraction_id.name")
    fraction_material = fields.Char(related="fraction_id.material")
    is_bundle = fields.Boolean(string="Es un combo?", required=True, default=False)
    bundle_items = fields.One2many('cmp.sale.items', 'bundle_id', string='Items del combo')


class SorterRule(models.Model):
    _name = "cmp.sorter.rule"
    _description = "Regla para preparar paquetes"

    name = fields.Char(string='Nombre Regla', required=True, translate=True)
    max_units = fields.Integer(string='Cantidad Maxima Permitida por Destinatario', required=True, translate=True)
    max_unit_weight = fields.Float(string='Peso Maximo Permitido (kg)', translate=True)
    max_points = fields.Float(string='Maximo de Puntos en Aduana', translate=True, default=0)
    price_unit = fields.Float(string='Precio x UM', translate=True)
    uom_package = fields.Selection([("m3", "m3"), ("unidad", "unidad"), ("kg", "kg")], string="UM")
    one_bag = fields.Boolean(string='Un solo bulto', default=True)
    show_generic = fields.Boolean(string='Mostrar tipo generico', default=False)


class SaleItems(models.Model):
    _name = "cmp.sale.items"
    _description = "Listado de articulos de venta para procesar"

    name = fields.Char(string="Descripcion", default="")
    item_id = fields.Many2one('product.template', string='Producto', translate=True)
    barcode = fields.Char()
    category_id = fields.Many2one('cmp.category.item',
                                  string='Categoria Aduana', related='item_id.category_id', translate=True)
    description = fields.Text(string='Descripcion', translate=True)
    weight = fields.Float(string='Peso kg', translate=True, default=0)
    quantity = fields.Float(string='Cantidad',
                            required=True,
                            translate=True, default=0)
    volume = fields.Float(string="Volumen", default=0)
    package_id = fields.Many2one('cmp.package.items', string='Paquete', translate=True, ondelete='cascade')
    total_envoy_id = fields.Many2one('cmp.envoy.total', string='Envio total', ondelete='cascade')
    bundle_id = fields.Many2one('product.template', string='Combo', ondelete='cascade')
    max_allowed = fields.Float(related="category_id.max_count", string="Cantd Permitida")
    price_unit = fields.Float("Precio unitario MN")
    no_serie = fields.Char(string="No Serie")
    bags = fields.Integer(string='Bultos que lo componen', default=1)

    # @api.depends('item_id')
    # def _compute_name(self):
    #     for item in self:
    #         if item.item_id.name:
    #             item.name = item.item_id.name + " - " + str(item.quantity)

    @api.onchange('item_id')
    def onchange_item(self):
        self.weight = self.item_id.weight
        self.volume = self.item_id.volume
