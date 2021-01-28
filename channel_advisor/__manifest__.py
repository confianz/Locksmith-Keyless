# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Channel Advisor Integration',
    'version': '1.0',
    'category': 'Sales',
    'author'  : "Confianz Global",
    'sequence': 1500,
    'summary': 'The module that manages the Channel Advisor ',
    'description': """
The module that manages the order generated via Channel Advisor
    """,
    'website': 'https://www.confianzit.com',
    'depends': ['sale','sale_margin'],
    'data': [
        'views/edi_config_view.xml',
        'views/sale_order_view.xml',
        'views/partner_view.xml',
        'views/edi_log_view.xml',
        'views/product_view.xml',
        'views/menu.xml',
        'views/connector_views.xml',
        "data/order_import_cron.xml",
        'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
