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
    'depends': ['stock', 'report_glabels', 'web_widget_many2many_tags_open'],
    'conflicts': ['stock_quant_expand'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/stock_package_add.xml',
            'wizard/stock_package_move.xml',
            'wizard/stock_package_picking.xml',
            'wizard/stock_package_get.xml',
            'wizard/sale_order_package_add.xml',
            'views/product_template_view.xml',
            'views/stock_move_views.xml',
            'views/stock_production_lot_views.xml',
            'views/stock_picking_package_views.xml',
            'views/stock_picking_views.xml',
            'views/stock_quant_views.xml',
        ],
    'demo': [
             ],
    "license" : "AGPL-3",
    'installable': True,
}
