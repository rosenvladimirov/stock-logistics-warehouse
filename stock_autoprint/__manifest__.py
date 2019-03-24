# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Glabels Reports Autoprint',
    'version': '11.0.0.1',
    'category': 'Reporting',
    'summary': 'Auto print glabel reports',
    'description': """
""",
    'author': 'Rosen Vladimirov',
    'depends': ['stock', 'report_glabels'],
    'data': [
            'views/product_template_view.xml',
            'views/stock_move_views.xml',
            'views/stock_production_lot_views.xml',
            'views/stock_picking_views.xml',
             ],
    'demo': [
             ],
    "license" : "AGPL-3",
    'installable': True,
}
