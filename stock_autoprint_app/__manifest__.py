# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Glabels Reports Autoprint app',
    'version': '11.0.0.1',
    'category': 'Reporting',
    'summary': 'Auto print glabel reports app',
    'description': """
""",
    'author': 'Rosen Vladimirov',
    'depends': ['stock_autoprint'],
    'data': [
        'views/stock_autoprint_views.xml',
        ],
    'demo': [
             ],
    "license" : "AGPL-3",
    'installable': True,
    'application': True,
}
