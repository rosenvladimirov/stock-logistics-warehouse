# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Glabels Reports Autoprint peoduct sets',
    'version': '11.0.0.1',
    'category': 'Reporting',
    'summary': 'Auto print glabel reports product sets',
    'description': """
""",
    'author': 'Rosen Vladimirov',
    'depends': ['stock_autoprint', 'sale_product_set'],
    'data': [
        'wizard/stock_package_from_set.xml',
        'views/stock_quant_views.xml',
        'views/sale_order.xml',
    ],
    'demo': [
             ],
    "license" : "AGPL-3",
    'installable': True,
}
