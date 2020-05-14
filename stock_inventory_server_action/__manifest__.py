# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Stock inventory validate at background",
    'summary': "Add support for barcode scanning in workorder.",
    'description': """
        Stock inventory action validate on server.
    """,
    'category': 'Warehouse',
    'version': '11.0.0.1.0',
    'author': 'Rosen Vladimirov, '
              'BioPrint Ltd.',
    'depends': ['stock', 'stock_inventory_chatter'],
    'data': [
        'data/stock_inventory_server_action.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'AGPL-3',
}
