# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Frezee packages (instruments)',
    'version': '11.0.0.1',
    'category': 'Reporting',
    'summary': 'Auto print glabel reports app',
    'description': """
""",
    'author': 'Rosen Vladimirov, '
              'BioPrint Ltd.',
    'depends': ['stock_autoprint'],
    'data': [
        'views/product_packaging_view.xml',
        'views/stock_autoprint_views.xml',
        ],
    'demo': [
             ],
    "license" : "AGPL-3",
    'installable': True,
    'application': True,
}
