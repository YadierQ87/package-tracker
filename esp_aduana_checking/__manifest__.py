# -*- coding: utf-8 -*-
{
    'name': "esp_aduana_checking",

    'summary': """
        Chequeo de paquetes enviados por el transitario en la esp_aduana_checking""",

    'description': """
        Se utiliza para chequear a traves de codigos de barra los paquetes enviados por un transitario
    """,

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
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
