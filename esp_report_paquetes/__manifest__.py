# -*- coding: utf-8 -*-
{
    'name': "esp_report_paquetes",

    'summary': """
        Chequeo de paquetes enviados por el transitario en la esp_report_paquetes""",

    'description': """
        Se utiliza para reportar la cantd de paquetes de 1.5kg por provincias y municipios""",

    'author': "Yadier , Pepe y Lazarito (Espiral)",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customs',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','esp_componedor_paquetes'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
}
