# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Stock Picking Internal Move",
    "version": "11.0.1.0.0",
    "author": "Rosen Vladimirov, "
              "Bioprint Ltd.",
    "website": "https://github.com/rosenvladimirov/stock-logistics-warehouse",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        'stock',
        'stock_autoprint',
    ],
    "data": [
        'wizard/stock_import_picking.xml',
        'views/stock_picking_views.xml',
    ],
    "installable": True,
}
