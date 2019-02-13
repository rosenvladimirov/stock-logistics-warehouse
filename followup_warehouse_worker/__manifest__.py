# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Follow-up warehouse worker',
    'version': '11.0.1.0',
    'category': 'Warehouse',
    'summary': 'Notification of a worker in the warehouse for warehouse movements',
    'description': """
    """,
    'depends': ['sale', 'website_sale'],
    'data': [
        'views/stock_location_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
